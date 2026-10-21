"""Fixtures compartilhadas: dados de exemplo e uma OpenF1 falsa (sem rede)."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx
import pytest

from f1.client import OpenF1Client

FIXTURES = Path(__file__).parent / "fixtures"

#: (endpoint, filtro, valor) -> arquivo em ``tests/fixtures``.
ROTAS = {
    ("meetings", "year", "2023"): "meetings_2023.json",
    ("sessions", "meeting_key", "1219"): "sessions_1219.json",
    ("session_result", "session_key", "9161"): "session_result_9161.json",
    ("session_result", "session_key", "9165"): "session_result_9165.json",
    ("drivers", "session_key", "9161"): "drivers_9165.json",
    ("drivers", "session_key", "9165"): "drivers_9165.json",
}


def ler_fixture(nome: str) -> Any:
    return json.loads((FIXTURES / nome).read_text(encoding="utf-8"))


def responder_openf1(request: httpx.Request) -> httpx.Response:
    """Imita a OpenF1: devolve a fixture da rota ou 404 "No results found."."""
    endpoint = request.url.path.rsplit("/", 1)[-1]
    for (rota, filtro, valor), arquivo in ROTAS.items():
        if rota == endpoint and request.url.params.get(filtro) == valor:
            return httpx.Response(200, json=ler_fixture(arquivo))
    return httpx.Response(404, json={"detail": "No results found."})


@pytest.fixture
def dados_api() -> Callable[[str], Any]:
    """Leitor das fixtures JSON (ex.: ``dados_api("drivers_9165.json")``)."""
    return ler_fixture


@pytest.fixture
def api_falsa() -> Callable[[httpx.Request], httpx.Response]:
    """Handler da OpenF1 falsa, para compor com respostas de erro nos testes."""
    return responder_openf1


@pytest.fixture
def criar_cliente() -> Callable[..., OpenF1Client]:
    """Fábrica de ``OpenF1Client`` com transporte falso (padrão: a OpenF1 falsa).

    As pausas entre tentativas são ignoradas, salvo se ``esperar`` for passado.
    """

    def fabrica(
        handler: Callable[[httpx.Request], httpx.Response] = responder_openf1,
        **opcoes: Any,
    ) -> OpenF1Client:
        opcoes.setdefault("esperar", lambda segundos: None)
        return OpenF1Client(
            http_client=httpx.Client(transport=httpx.MockTransport(handler)),
            **opcoes,
        )

    return fabrica
