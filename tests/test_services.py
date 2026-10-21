from datetime import UTC, datetime

import pytest

from f1.models import Driver, Meeting, Session, SessionResult
from f1.services import (
    COLUNAS,
    COR_PADRAO,
    cor_texto_contraste,
    formatar_tempo,
    melhor_fase,
    montar_classificacao,
    ordenar_meetings,
    ordenar_sessoes,
    status,
)


@pytest.fixture
def pilotos(dados_api):
    return [Driver.from_api(d) for d in dados_api("drivers_9165.json")]


def _resultados(dados_api, arquivo):
    return [SessionResult.from_api(r) for r in dados_api(arquivo)]


# --- ordenação de meetings e sessões -------------------------------------


def test_ordenar_meetings_remove_cancelados_e_ordena_por_data(dados_api):
    meetings = [Meeting.from_api(m) for m in dados_api("meetings_2023.json")]

    ordenados = ordenar_meetings(meetings)

    assert [m.meeting_name for m in ordenados] == [
        "Italian Grand Prix",
        "Singapore Grand Prix",
        "Japanese Grand Prix",
    ]


def test_ordenar_meetings_coloca_sem_data_no_fim():
    sem_data = Meeting(meeting_key=1, meeting_name="A definir", year=2023)
    com_data = Meeting(
        meeting_key=2,
        meeting_name="GP",
        year=2023,
        date_start=datetime(2023, 3, 5, tzinfo=UTC),
    )

    assert ordenar_meetings([sem_data, com_data]) == [com_data, sem_data]


def test_ordenar_sessoes_ordena_e_remove_canceladas(dados_api):
    sessoes = [Session.from_api(s) for s in reversed(dados_api("sessions_1219.json"))]
    cancelada = Session(
        session_key=1, session_name="Sprint", meeting_key=1219, is_cancelled=True
    )

    ordenadas = ordenar_sessoes([*sessoes, cancelada])

    assert [s.session_name for s in ordenadas] == [
        "Practice 1",
        "Practice 2",
        "Practice 3",
        "Qualifying",
        "Race",
    ]


# --- formatação --------------------------------------------------------------


@pytest.mark.parametrize(
    ("segundos", "esperado"),
    [
        (0, "0:00.000"),
        (9.5, "0:09.500"),
        (90.984, "1:30.984"),
        (92.12, "1:32.120"),
        (59.9996, "1:00.000"),
        (3599.999, "59:59.999"),
        (6397.418, "1:46:37.418"),
    ],
)
def test_formatar_tempo(segundos, esperado):
    assert formatar_tempo(segundos) == esperado


def test_formatar_tempo_rejeita_negativo():
    with pytest.raises(ValueError, match="negativo"):
        formatar_tempo(-1)


@pytest.mark.parametrize(
    ("fundo", "texto"),
    [
        ("#FFFFFF", "#000000"),
        ("6CD3BF", "#000000"),  # Mercedes
        ("#F58020", "#000000"),  # McLaren
        ("#3671C6", "#FFFFFF"),  # Red Bull
        ("#000000", "#FFFFFF"),
    ],
)
def test_cor_texto_contraste(fundo, texto):
    assert cor_texto_contraste(fundo) == texto


def test_cor_texto_contraste_rejeita_cor_invalida():
    with pytest.raises(ValueError, match="Cor inválida"):
        cor_texto_contraste("#FFF")


# --- melhor fase e status ------------------------------------------------


@pytest.mark.parametrize(
    ("duracao", "gap", "esperado"),
    [
        # corrida / treino: valores escalares
        (6397.418, 0, (6397.418, 0)),
        (6398.23, 0.812, (6398.23, 0.812)),
        (None, "+1 LAP", (None, "+1 LAP")),
        (None, None, (None, None)),
        # classificação: última fase com tempo
        ([92.339, 91.439, 90.984], [0.348, 0.0, 0.0], (90.984, 0.0)),
        ([92.452, 92.274, None], [0.461, 0.835, None], (92.274, 0.835)),
        ([93.252, None, None], [1.261, None, None], (93.252, 1.261)),
        ([None, None, None], [None, None, None], (None, None)),
        ([93.0, 92.0], None, (92.0, None)),
    ],
)
def test_melhor_fase(duracao, gap, esperado):
    resultado = SessionResult(driver_number=1, duration=duracao, gap_to_leader=gap)
    assert melhor_fase(resultado) == esperado


@pytest.mark.parametrize(
    ("flags", "esperado"),
    [
        ({}, "Classificado"),
        ({"dnf": True}, "DNF"),
        ({"dns": True}, "DNS"),
        ({"dsq": True}, "DSQ"),
        ({"dnf": True, "dsq": True}, "DSQ"),
    ],
)
def test_status(flags, esperado):
    assert status(SessionResult(driver_number=1, **flags)) == esperado


# --- montar_classificacao ----------------------------------------------------


def test_classificacao_da_corrida(dados_api, pilotos):
    tabela = montar_classificacao(
        _resultados(dados_api, "session_result_9165.json"), pilotos
    )

    assert list(tabela.columns) == COLUNAS
    assert list(tabela["Sigla"][:3]) == ["SAI", "NOR", "HAM"]
    primeiro = tabela.iloc[0]
    assert primeiro["Piloto"] == "Carlos SAINZ"
    assert primeiro["Equipe"] == "Ferrari"
    assert primeiro["Cor"] == "#F91536"
    assert primeiro["Tempo"] == "1:46:37.418"
    assert primeiro["Gap"] == "Líder"
    assert primeiro["Gap (s)"] == 0
    assert primeiro["Voltas"] == 62
    assert primeiro["Status"] == "Classificado"
    assert tabela.iloc[1]["Gap"] == "+0.812"


def test_classificacao_da_corrida_trata_abandonos(dados_api, pilotos):
    tabela = montar_classificacao(
        _resultados(dados_api, "session_result_9165.json"), pilotos
    )

    russell = tabela[tabela["Sigla"] == "RUS"].iloc[0]
    assert russell["Posição"] == 16
    assert russell["Status"] == "DNF"
    assert russell["Tempo"] == ""
    assert russell["Gap"] == ""

    # sem posição: vão para o fim, na ordem da API
    assert list(tabela["Sigla"][-2:]) == ["BOT", "TSU"]
    assert tabela["Posição"][-2:].isna().all()


def test_classificacao_do_quali_usa_ultima_fase(dados_api, pilotos):
    tabela = montar_classificacao(
        _resultados(dados_api, "session_result_9161.json"), pilotos
    )

    por_sigla = tabela.set_index("Sigla")
    assert por_sigla.loc["SAI", "Tempo"] == "1:30.984"
    assert por_sigla.loc["SAI", "Gap"] == "Líder"
    assert por_sigla.loc["GAS", "Tempo"] == "1:32.274"  # eliminado no Q2
    assert por_sigla.loc["GAS", "Gap"] == "+0.835"
    assert por_sigla.loc["SAR", "Tempo"] == "1:33.252"  # eliminado no Q1
    assert por_sigla.loc["SAR", "Gap (s)"] == pytest.approx(1.261)


def test_classificacao_mostra_retardatario_com_voltas_de_atraso():
    resultados = [
        SessionResult(driver_number=1, position=1, duration=5400.0, gap_to_leader=0),
        SessionResult(
            driver_number=2, position=2, gap_to_leader="+1 LAP", number_of_laps=56
        ),
        SessionResult(driver_number=3, position=3, gap_to_leader="+2 LAPS"),
    ]

    tabela = montar_classificacao(resultados, [])

    assert list(tabela["Gap"]) == ["Líder", "+1 LAP", "+2 LAPS"]
    assert tabela["Gap (s)"].isna().tolist() == [False, True, True]


def test_classificacao_ordena_por_posicao():
    resultados = [
        SessionResult(driver_number=3, position=3),
        SessionResult(driver_number=9, position=None, dns=True),
        SessionResult(driver_number=1, position=1),
        SessionResult(driver_number=2, position=2),
    ]

    tabela = montar_classificacao(resultados, [])

    assert list(tabela["Número"]) == [1, 2, 3, 9]
    assert tabela.iloc[-1]["Status"] == "DNS"


def test_classificacao_com_piloto_ausente_em_drivers():
    resultados = [SessionResult(driver_number=99, position=1, duration=80.0)]
    pilotos = [Driver(driver_number=1, full_name="Outro", team_colour="3671C6")]

    linha = montar_classificacao(resultados, pilotos).iloc[0]

    assert linha["Sigla"] == "99"
    assert linha["Piloto"] == "#99"
    assert linha["Equipe"] == ""
    assert linha["Cor"] == COR_PADRAO


def test_classificacao_vazia_mantem_colunas():
    tabela = montar_classificacao([], [])

    assert tabela.empty
    assert list(tabela.columns) == COLUNAS
