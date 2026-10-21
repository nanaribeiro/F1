"""Cliente HTTP da API OpenF1 (https://openf1.org)."""

from __future__ import annotations

import re
import time
from collections.abc import Callable, Mapping
from typing import Any
from urllib.parse import quote

import httpx

from f1.models import Driver, Meeting, Session, SessionResult

BASE_URL = "https://api.openf1.org/v1"

#: Separa o nome do filtro de um operador opcional, ex.: ``"position<="``.
_FILTRO = re.compile(r"^(?P<campo>\w+)(?P<operador>>=|<=|>|<|=)?$")

#: Mensagem devolvida pela API (com status 404) quando a consulta é vazia.
_SEM_RESULTADOS = "No results found."


class OpenF1Error(Exception):
    """Falha ao consultar a API OpenF1 (HTTP, rede ou resposta inválida)."""


def _formatar_valor(valor: Any) -> str:
    if isinstance(valor, bool):
        return "true" if valor else "false"
    return str(valor)


def _pausa(resposta: httpx.Response, tentativa: int) -> float:
    """Segundos de espera antes de repetir uma resposta 429.

    Usa o cabeçalho ``Retry-After`` (em segundos) quando presente; senão,
    espera 1 s, 2 s, 3 s... conforme a tentativa.
    """
    try:
        return max(0.0, float(resposta.headers["Retry-After"]))
    except (KeyError, ValueError):
        return float(tentativa)


def montar_query(filtros: Mapping[str, Any]) -> str:
    """Monta a query string da OpenF1 a partir de ``filtros``.

    A chave pode terminar com um operador (``>=``, ``<=``, ``>``, ``<``),
    por exemplo ``{"position<=": 3}``. Valores em lista ou tupla geram o
    parâmetro repetido (``driver_number=4&driver_number=81``). Valores
    ``None`` são ignorados.
    """
    partes: list[str] = []
    for chave, valor in filtros.items():
        correspondencia = _FILTRO.match(chave)
        if correspondencia is None:
            raise ValueError(f"Filtro inválido: {chave!r}")
        campo = correspondencia["campo"]
        operador = correspondencia["operador"] or "="
        valores = valor if isinstance(valor, list | tuple) else [valor]
        partes.extend(
            f"{campo}{operador}{quote(_formatar_valor(item), safe='')}"
            for item in valores
            if item is not None
        )
    return "&".join(partes)


class OpenF1Client:
    """Cliente para os endpoints da OpenF1 usados pelo dashboard.

    Args:
        base_url: URL base da API.
        timeout: tempo máximo de cada requisição, em segundos.
        http_client: ``httpx.Client`` opcional (útil para testes com
            ``httpx.MockTransport``). Se omitido, um cliente é criado.
        tentativas: número máximo de tentativas quando a API responde 429
            (limite de requisições por segundo).
        esperar: função que pausa por N segundos entre tentativas
            (padrão: ``time.sleep``; substituível nos testes).
    """

    def __init__(
        self,
        base_url: str = BASE_URL,
        timeout: float = 10.0,
        http_client: httpx.Client | None = None,
        tentativas: int = 3,
        esperar: Callable[[float], None] = time.sleep,
    ) -> None:
        if tentativas < 1:
            raise ValueError("É preciso ao menos uma tentativa.")
        self.base_url = base_url.rstrip("/")
        self._http = http_client or httpx.Client(timeout=timeout)
        self._tentativas = tentativas
        self._esperar = esperar

    def montar_url(self, endpoint: str, filtros: Mapping[str, Any] | None) -> str:
        url = f"{self.base_url}/{endpoint.strip('/')}"
        query = montar_query(filtros or {})
        return f"{url}?{query}" if query else url

    def _get(
        self, endpoint: str, filtros: Mapping[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Executa um ``GET`` e devolve a lista JSON da resposta.

        Consultas sem resultado (404 com ``"No results found."``) devolvem
        lista vazia. Respostas 429 são repetidas após uma pausa. Qualquer
        outra falha vira ``OpenF1Error``.
        """
        url = self.montar_url(endpoint, filtros)
        for tentativa in range(1, self._tentativas + 1):
            try:
                resposta = self._http.get(url)
            except httpx.HTTPError as erro:
                raise OpenF1Error(f"Falha de rede ao acessar {url}: {erro}") from erro
            if resposta.status_code != 429 or tentativa == self._tentativas:
                break
            self._esperar(_pausa(resposta, tentativa))

        if resposta.status_code == 404 and self._sem_resultados(resposta):
            return []
        if resposta.is_error:
            raise OpenF1Error(
                f"A API respondeu {resposta.status_code} para {url}: "
                f"{resposta.text[:200]}"
            )

        try:
            dados = resposta.json()
        except ValueError as erro:
            raise OpenF1Error(f"Resposta JSON inválida de {url}") from erro
        if not isinstance(dados, list):
            raise OpenF1Error(f"Resposta inesperada de {url}: {str(dados)[:200]}")
        return dados

    @staticmethod
    def _sem_resultados(resposta: httpx.Response) -> bool:
        try:
            corpo = resposta.json()
        except ValueError:
            return False
        return isinstance(corpo, dict) and corpo.get("detail") == _SEM_RESULTADOS

    def meetings(self, year: int) -> list[Meeting]:
        return [Meeting.from_api(m) for m in self._get("meetings", {"year": year})]

    def sessions(self, meeting_key: int) -> list[Session]:
        dados = self._get("sessions", {"meeting_key": meeting_key})
        return [Session.from_api(s) for s in dados]

    def session_result(self, session_key: int) -> list[SessionResult]:
        dados = self._get("session_result", {"session_key": session_key})
        return [SessionResult.from_api(r) for r in dados]

    def drivers(self, session_key: int) -> list[Driver]:
        dados = self._get("drivers", {"session_key": session_key})
        return [Driver.from_api(d) for d in dados]

    def close(self) -> None:
        self._http.close()
