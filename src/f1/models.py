"""Modelos de domínio construídos a partir das respostas da API OpenF1.

Cada modelo expõe ``from_api``, que recebe um item JSON da API, lê apenas os
campos usados pelo projeto e ignora os demais (inclusive os deprecados, como
``country_code``). Campos de identificação são obrigatórios e geram
``KeyError`` se ausentes; os demais recebem valores padrão.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

#: Valor de ``duration`` na API: número (corrida/treino), lista [Q1, Q2, Q3]
#: (classificação) ou nulo.
Duracao = float | list[float | None] | None

#: Valor de ``gap_to_leader`` na API: número, texto ``"+N LAP(S)"``,
#: lista [Q1, Q2, Q3] (classificação) ou nulo.
Gap = float | str | list[float | str | None] | None


def _parse_data(valor: str | None) -> datetime | None:
    """Converte uma data ISO 8601 da API em ``datetime`` (ou ``None``)."""
    return datetime.fromisoformat(valor) if valor else None


@dataclass(frozen=True)
class Meeting:
    """Fim de semana de GP ou de testes."""

    meeting_key: int
    meeting_name: str
    year: int
    date_start: datetime | None = None
    country_name: str | None = None
    location: str | None = None
    circuit_short_name: str | None = None
    is_cancelled: bool = False

    @classmethod
    def from_api(cls, dados: dict[str, Any]) -> Meeting:
        return cls(
            meeting_key=dados["meeting_key"],
            meeting_name=dados["meeting_name"],
            year=dados["year"],
            date_start=_parse_data(dados.get("date_start")),
            country_name=dados.get("country_name"),
            location=dados.get("location"),
            circuit_short_name=dados.get("circuit_short_name"),
            is_cancelled=bool(dados.get("is_cancelled", False)),
        )


@dataclass(frozen=True)
class Session:
    """Sessão de um meeting (treino, classificação, sprint, corrida)."""

    session_key: int
    session_name: str
    meeting_key: int
    session_type: str | None = None
    date_start: datetime | None = None
    is_cancelled: bool = False

    @classmethod
    def from_api(cls, dados: dict[str, Any]) -> Session:
        return cls(
            session_key=dados["session_key"],
            session_name=dados["session_name"],
            meeting_key=dados["meeting_key"],
            session_type=dados.get("session_type"),
            date_start=_parse_data(dados.get("date_start")),
            is_cancelled=bool(dados.get("is_cancelled", False)),
        )

    @property
    def is_qualifying(self) -> bool:
        """Indica se a sessão usa o formato de classificação [Q1, Q2, Q3]."""
        return self.session_type == "Qualifying"


@dataclass(frozen=True)
class Driver:
    """Piloto participante de uma sessão."""

    driver_number: int
    full_name: str | None = None
    name_acronym: str | None = None
    team_name: str | None = None
    team_colour: str | None = None

    @classmethod
    def from_api(cls, dados: dict[str, Any]) -> Driver:
        return cls(
            driver_number=dados["driver_number"],
            full_name=dados.get("full_name"),
            name_acronym=dados.get("name_acronym"),
            team_name=dados.get("team_name"),
            team_colour=dados.get("team_colour"),
        )


@dataclass(frozen=True)
class Lap:
    """Volta de um piloto em uma sessão."""

    session_key: int
    driver_number: int
    lap_number: int
    lap_duration: float | None = None
    duration_sector_1: float | None = None
    duration_sector_2: float | None = None
    duration_sector_3: float | None = None
    is_pit_out_lap: bool = False

    @classmethod
    def from_api(cls, dados: dict[str, Any]) -> Lap:
        return cls(
            session_key=dados["session_key"],
            driver_number=dados["driver_number"],
            lap_number=dados["lap_number"],
            lap_duration=dados.get("lap_duration"),
            duration_sector_1=dados.get("duration_sector_1"),
            duration_sector_2=dados.get("duration_sector_2"),
            duration_sector_3=dados.get("duration_sector_3"),
            is_pit_out_lap=bool(dados.get("is_pit_out_lap", False)),
        )


@dataclass(frozen=True)
class SessionResult:
    """Resultado final de um piloto em uma sessão."""

    driver_number: int
    position: int | None = None
    duration: Duracao = None
    gap_to_leader: Gap = None
    number_of_laps: int | None = None
    dnf: bool = False
    dns: bool = False
    dsq: bool = False

    @classmethod
    def from_api(cls, dados: dict[str, Any]) -> SessionResult:
        return cls(
            driver_number=dados["driver_number"],
            position=dados.get("position"),
            duration=dados.get("duration"),
            gap_to_leader=dados.get("gap_to_leader"),
            number_of_laps=dados.get("number_of_laps"),
            dnf=bool(dados.get("dnf", False)),
            dns=bool(dados.get("dns", False)),
            dsq=bool(dados.get("dsq", False)),
        )
