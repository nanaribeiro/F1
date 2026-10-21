from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from f1.models import Driver, Meeting, Session, SessionResult


def test_meeting_from_api_le_campos_usados(dados_api):
    singapura = dados_api("meetings_2023.json")[2]

    meeting = Meeting.from_api(singapura)

    assert meeting == Meeting(
        meeting_key=1219,
        meeting_name="Singapore Grand Prix",
        year=2023,
        date_start=datetime(2023, 9, 15, 9, 30, tzinfo=UTC),
        country_name="Singapore",
        location="Marina Bay",
        circuit_short_name="Singapore",
        is_cancelled=False,
    )


def test_meeting_from_api_le_cancelamento(dados_api):
    imola = dados_api("meetings_2023.json")[1]
    assert Meeting.from_api(imola).is_cancelled is True


def test_from_api_ignora_campos_desconhecidos_e_deprecados():
    piloto = Driver.from_api(
        {"driver_number": 1, "country_code": "NED", "campo_novo": [1, 2]}
    )

    assert piloto == Driver(driver_number=1)
    assert not hasattr(piloto, "country_code")


def test_from_api_usa_padroes_para_campos_opcionais_ausentes():
    assert Meeting.from_api(
        {"meeting_key": 1, "meeting_name": "GP", "year": 2024}
    ) == Meeting(meeting_key=1, meeting_name="GP", year=2024)
    assert SessionResult.from_api({"driver_number": 44}) == SessionResult(
        driver_number=44
    )


@pytest.mark.parametrize(
    ("modelo", "dados"),
    [
        (Meeting, {"meeting_name": "GP", "year": 2024}),
        (Session, {"session_key": 1, "session_name": "Race"}),
        (Driver, {"full_name": "Sem Número"}),
        (SessionResult, {"position": 1}),
    ],
)
def test_from_api_exige_campos_de_identificacao(modelo, dados):
    with pytest.raises(KeyError):
        modelo.from_api(dados)


def test_session_from_api_e_is_qualifying(dados_api):
    sessoes = [Session.from_api(s) for s in dados_api("sessions_1219.json")]
    por_nome = {s.session_name: s for s in sessoes}

    assert por_nome["Qualifying"].is_qualifying
    assert not por_nome["Race"].is_qualifying
    assert por_nome["Race"].session_key == 9165
    assert por_nome["Race"].date_start == datetime(2023, 9, 17, 12, tzinfo=UTC)


def test_session_result_from_api_mantem_listas_da_classificacao(dados_api):
    pole = SessionResult.from_api(dados_api("session_result_9161.json")[0])

    assert pole.duration == [92.339, 91.439, 90.984]
    assert pole.gap_to_leader == [0.348, 0.0, 0.0]


def test_modelos_sao_imutaveis():
    piloto = Driver(driver_number=1)
    with pytest.raises(FrozenInstanceError):
        piloto.driver_number = 2  # type: ignore[misc]
