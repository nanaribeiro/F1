from urllib.parse import unquote

import httpx
import pytest

from f1.client import BASE_URL, OpenF1Client, OpenF1Error, montar_query
from f1.models import Driver, Meeting, Session, SessionResult


@pytest.mark.parametrize(
    ("filtros", "esperado"),
    [
        ({}, ""),
        ({"session_key": 9165}, "session_key=9165"),
        ({"position<=": 3}, "position<=3"),
        ({"speed>=": 315}, "speed>=315"),
        ({"interval>": 0, "interval<": 0.005}, "interval>0&interval<0.005"),
        ({"driver_number": [4, 81]}, "driver_number=4&driver_number=81"),
        ({"driver_number": (1, 55)}, "driver_number=1&driver_number=55"),
        ({"is_pit_out_lap": True}, "is_pit_out_lap=true"),
        ({"dnf": False}, "dnf=false"),
        ({"session_name": "Sprint Qualifying"}, "session_name=Sprint%20Qualifying"),
        ({"date_start>=": "2023-09-01"}, "date_start>=2023-09-01"),
        ({"year": 2023, "country_name": None}, "year=2023"),
    ],
)
def test_montar_query(filtros, esperado):
    assert montar_query(filtros) == esperado


@pytest.mark.parametrize("chave", ["", "position=<", "campo com espaco", "a!=1"])
def test_montar_query_rejeita_filtro_invalido(chave):
    with pytest.raises(ValueError, match="Filtro inválido"):
        montar_query({chave: 1})


def test_montar_url_sem_filtros_nao_tem_interrogacao():
    cliente = OpenF1Client(base_url="https://exemplo.test/v1/")
    assert cliente.montar_url("/meetings", None) == "https://exemplo.test/v1/meetings"


def test_montar_url_usa_base_padrao():
    cliente = OpenF1Client()
    url = cliente.montar_url("session_result", {"session_key": 1, "position<=": 3})
    assert url == f"{BASE_URL}/session_result?session_key=1&position<=3"


def test_get_envia_operadores_e_valores_repetidos(criar_cliente):
    requisicoes: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requisicoes.append(request)
        return httpx.Response(200, json=[])

    cliente = criar_cliente(handler)
    cliente._get("session_result", {"position<=": 3, "driver_number": [4, 81]})

    (requisicao,) = requisicoes
    assert requisicao.url.path == "/v1/session_result"
    assert unquote(requisicao.url.query.decode()) == (
        "position<=3&driver_number=4&driver_number=81"
    )


def test_meetings_converte_resposta_em_modelos(criar_cliente):
    meetings = criar_cliente().meetings(2023)

    assert all(isinstance(m, Meeting) for m in meetings)
    assert [m.meeting_key for m in meetings] == [1220, 1209, 1219, 1218]


def test_sessions_converte_resposta_em_modelos(criar_cliente):
    sessoes = criar_cliente().sessions(1219)

    assert all(isinstance(s, Session) for s in sessoes)
    assert [s.session_name for s in sessoes][-1] == "Race"


def test_session_result_e_drivers(criar_cliente):
    cliente = criar_cliente()

    resultados = cliente.session_result(9165)
    pilotos = cliente.drivers(9165)

    assert all(isinstance(r, SessionResult) for r in resultados)
    assert resultados[0].driver_number == 55
    assert all(isinstance(p, Driver) for p in pilotos)
    assert {p.name_acronym for p in pilotos} >= {"SAI", "NOR", "HAM"}


def test_consulta_sem_resultados_devolve_lista_vazia(criar_cliente):
    assert criar_cliente().session_result(123456) == []


@pytest.mark.parametrize(
    "resposta",
    [
        httpx.Response(404, json={"detail": "Not Found"}),
        httpx.Response(404, text="página inexistente"),
        httpx.Response(429, json={"detail": "Too many requests"}),
        httpx.Response(500, text="erro interno"),
        httpx.Response(503),
    ],
)
def test_status_de_erro_gera_openf1error(criar_cliente, resposta):
    cliente = criar_cliente(lambda request: resposta)

    with pytest.raises(OpenF1Error, match=str(resposta.status_code)):
        cliente.meetings(2023)


def _respostas_em_sequencia(*respostas: httpx.Response):
    """Handler que devolve ``respostas`` em ordem e registra as requisições."""
    fila = list(respostas)
    requisicoes: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requisicoes.append(request)
        return fila.pop(0)

    return handler, requisicoes


@pytest.mark.parametrize(
    ("cabecalhos", "pausa_esperada"),
    [
        ({}, 1.0),
        ({"Retry-After": "2"}, 2.0),
        ({"Retry-After": "0.5"}, 0.5),
        ({"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"}, 1.0),  # data: ignorada
    ],
)
def test_limite_de_requisicoes_e_repetido_apos_pausa(
    criar_cliente, cabecalhos, pausa_esperada
):
    handler, requisicoes = _respostas_em_sequencia(
        httpx.Response(429, headers=cabecalhos, json={"detail": "Rate limit"}),
        httpx.Response(200, json=[{"driver_number": 1}]),
    )
    pausas: list[float] = []
    cliente = criar_cliente(handler, esperar=pausas.append)

    assert cliente.drivers(9165) == [Driver(driver_number=1)]
    assert len(requisicoes) == 2
    assert pausas == [pausa_esperada]


def test_limite_de_requisicoes_persistente_gera_openf1error(criar_cliente):
    handler, requisicoes = _respostas_em_sequencia(
        *[httpx.Response(429, json={"detail": "Rate limit"}) for _ in range(3)]
    )
    pausas: list[float] = []
    cliente = criar_cliente(handler, tentativas=3, esperar=pausas.append)

    with pytest.raises(OpenF1Error, match="429"):
        cliente.meetings(2023)
    assert len(requisicoes) == 3
    assert pausas == [1.0, 2.0]


def test_tentativas_precisa_ser_positivo():
    with pytest.raises(ValueError, match="ao menos uma tentativa"):
        OpenF1Client(tentativas=0)


@pytest.mark.parametrize(
    "excecao",
    [httpx.ReadTimeout("tempo esgotado"), httpx.ConnectError("sem conexão")],
)
def test_falha_de_rede_gera_openf1error(criar_cliente, excecao):
    def handler(request: httpx.Request) -> httpx.Response:
        raise excecao

    with pytest.raises(OpenF1Error, match="Falha de rede") as info:
        criar_cliente(handler).meetings(2023)
    assert info.value.__cause__ is excecao


def test_json_invalido_gera_openf1error(criar_cliente):
    cliente = criar_cliente(lambda request: httpx.Response(200, text="<html>"))

    with pytest.raises(OpenF1Error, match="JSON inválida"):
        cliente.drivers(9165)


def test_resposta_que_nao_e_lista_gera_openf1error(criar_cliente):
    cliente = criar_cliente(
        lambda request: httpx.Response(200, json={"detail": "inesperado"})
    )

    with pytest.raises(OpenF1Error, match="Resposta inesperada"):
        cliente.sessions(1219)


def test_close_fecha_cliente_http():
    http = httpx.Client()
    OpenF1Client(http_client=http).close()
    assert http.is_closed
