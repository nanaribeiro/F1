"""Regras de montagem do resultado das sessões (lógica pura, sem rede)."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from f1.models import Driver, Meeting, Session, SessionResult

COR_PADRAO = "#808080"

COLUNAS = [
    "Posição",
    "Número",
    "Sigla",
    "Piloto",
    "Equipe",
    "Cor",
    "Tempo",
    "Gap",
    "Gap (s)",
    "Voltas",
    "Status",
]


def _ordenar_por_data[T: (Meeting, Session)](itens: Iterable[T]) -> list[T]:
    """Remove itens cancelados e ordena por ``date_start`` (sem data no fim)."""
    ativos = [item for item in itens if not item.is_cancelled]
    return sorted(ativos, key=lambda item: (item.date_start is None, item.date_start))


def ordenar_meetings(meetings: Iterable[Meeting]) -> list[Meeting]:
    """Remove meetings cancelados e ordena cronologicamente."""
    return _ordenar_por_data(meetings)


def ordenar_sessoes(sessoes: Iterable[Session]) -> list[Session]:
    """Remove sessões canceladas e ordena cronologicamente."""
    return _ordenar_por_data(sessoes)


def formatar_tempo(segundos: float) -> str:
    """Formata segundos como ``m:ss.mmm`` (ou ``h:mm:ss.mmm`` a partir de 1 h).

    >>> formatar_tempo(90.984)
    '1:30.984'
    """
    if segundos < 0:
        raise ValueError("O tempo não pode ser negativo.")
    milissegundos = round(segundos * 1000)
    horas, resto = divmod(milissegundos, 3_600_000)
    minutos, resto = divmod(resto, 60_000)
    segs, ms = divmod(resto, 1000)
    if horas:
        return f"{horas}:{minutos:02d}:{segs:02d}.{ms:03d}"
    return f"{minutos}:{segs:02d}.{ms:03d}"


def melhor_fase(
    resultado: SessionResult,
) -> tuple[float | None, float | str | None]:
    """Devolve ``(tempo, gap)`` a exibir para um resultado.

    Em classificações, ``duration`` e ``gap_to_leader`` são listas
    [Q1, Q2, Q3]; usa-se a última fase em que o piloto marcou tempo. Nos
    demais tipos de sessão os valores são devolvidos como vieram.
    """
    duracao, gap = resultado.duration, resultado.gap_to_leader
    if not isinstance(duracao, list):
        return duracao, None if isinstance(gap, list) else gap

    gaps = gap if isinstance(gap, list) else []
    for indice in range(len(duracao) - 1, -1, -1):
        if duracao[indice] is not None:
            gap_fase = gaps[indice] if indice < len(gaps) else None
            return duracao[indice], gap_fase
    return None, None


def status(resultado: SessionResult) -> str:
    """Descreve a situação final do piloto na sessão."""
    if resultado.dsq:
        return "DSQ"
    if resultado.dns:
        return "DNS"
    if resultado.dnf:
        return "DNF"
    return "Classificado"


def _formatar_gap(gap: float | str | None, lider: bool) -> str:
    if lider:
        return "Líder"
    if gap is None:
        return ""
    if isinstance(gap, str):
        return gap
    return f"+{gap:.3f}"


def _cor(piloto: Driver | None) -> str:
    if piloto is None or not piloto.team_colour:
        return COR_PADRAO
    return f"#{piloto.team_colour.lstrip('#')}"


def cor_texto_contraste(cor_fundo: str) -> str:
    """Escolhe texto preto ou branco legível sobre ``cor_fundo`` (``#RRGGBB``)."""
    hex_cor = cor_fundo.lstrip("#")
    if len(hex_cor) != 6:
        raise ValueError(f"Cor inválida: {cor_fundo!r}")
    vermelho, verde, azul = (int(hex_cor[i : i + 2], 16) for i in (0, 2, 4))
    luminancia = 0.299 * vermelho + 0.587 * verde + 0.114 * azul
    return "#000000" if luminancia > 150 else "#FFFFFF"


def montar_classificacao(
    resultados: Iterable[SessionResult], pilotos: Iterable[Driver]
) -> pd.DataFrame:
    """Junta ``/session_result`` e ``/drivers`` por ``driver_number``.

    Pilotos sem posição (``position`` nula) vão para o fim, mantendo a ordem
    da API. Pilotos ausentes em ``/drivers`` aparecem com o número no lugar
    do nome e cor padrão.
    """
    por_numero = {piloto.driver_number: piloto for piloto in pilotos}
    ordenados = sorted(
        resultados,
        key=lambda r: (r.position is None, r.position or 0),
    )

    linhas = []
    for resultado in ordenados:
        piloto = por_numero.get(resultado.driver_number)
        tempo, gap = melhor_fase(resultado)
        linhas.append(
            {
                "Posição": resultado.position,
                "Número": resultado.driver_number,
                "Sigla": (piloto and piloto.name_acronym)
                or str(resultado.driver_number),
                "Piloto": (piloto and piloto.full_name)
                or f"#{resultado.driver_number}",
                "Equipe": (piloto and piloto.team_name) or "",
                "Cor": _cor(piloto),
                "Tempo": formatar_tempo(tempo) if tempo is not None else "",
                "Gap": _formatar_gap(gap, lider=resultado.position == 1),
                "Gap (s)": float(gap) if isinstance(gap, int | float) else None,
                "Voltas": resultado.number_of_laps,
                "Status": status(resultado),
            }
        )

    tabela = pd.DataFrame(linhas, columns=COLUNAS)
    tabela["Posição"] = tabela["Posição"].astype("Int64")
    tabela["Voltas"] = tabela["Voltas"].astype("Int64")
    tabela["Gap (s)"] = tabela["Gap (s)"].astype("float64")
    return tabela
