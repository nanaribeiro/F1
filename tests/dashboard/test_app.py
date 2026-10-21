"""Smoke tests do app Streamlit com a OpenF1 falsa (sem rede)."""

import json
from pathlib import Path

import httpx
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

import f1.dashboard
from f1.dashboard import ui

APP = str(Path(f1.dashboard.__file__).parent / "app.py")
TIMEOUT = 30  # a primeira execução importa pandas/plotly e pode passar de 3 s


def _novo_app() -> AppTest:
    return AppTest.from_file(APP, default_timeout=TIMEOUT)


@pytest.fixture(autouse=True)
def limpar_caches():
    st.cache_data.clear()
    st.cache_resource.clear()
    yield
    st.cache_data.clear()
    st.cache_resource.clear()


@pytest.fixture
def usar_cliente(monkeypatch, criar_cliente):
    """Faz o app usar um ``OpenF1Client`` com o transporte informado."""

    def aplicar(*args):
        monkeypatch.setattr(ui, "OpenF1Client", lambda: criar_cliente(*args))

    return aplicar


def _selecionar(app: AppTest, rotulo: str, opcao) -> None:
    caixa = next(s for s in app.sidebar.selectbox if s.label == rotulo)
    caixa.select_index(caixa.options.index(str(opcao))).run()


def _abrir_sessao(app: AppTest, sessao: str) -> AppTest:
    app.run()
    _selecionar(app, "Ano", 2023)
    _selecionar(app, "GP", "Singapore Grand Prix")
    _selecionar(app, "Sessão", sessao)
    return app


def test_ano_sem_gps_mostra_aviso(usar_cliente):
    usar_cliente()
    app = _novo_app().run()

    assert not app.exception
    assert "Nenhum GP encontrado" in app.sidebar.info[0].value


def test_lista_gps_em_ordem_e_sem_cancelados(usar_cliente):
    usar_cliente()
    app = _novo_app().run()
    _selecionar(app, "Ano", 2023)

    gp = next(s for s in app.sidebar.selectbox if s.label == "GP")
    assert gp.options == [
        "Italian Grand Prix",
        "Singapore Grand Prix",
        "Japanese Grand Prix",
    ]


def test_mostra_resultado_da_corrida(usar_cliente):
    usar_cliente()
    app = _abrir_sessao(_novo_app(), "Race")

    assert not app.exception
    assert app.subheader[0].value == "Singapore Grand Prix — Race"
    tabela = app.dataframe[0].value
    assert list(tabela["Sigla"][:3]) == ["SAI", "NOR", "HAM"]
    assert "Cor" not in tabela.columns
    assert len(app.get("plotly_chart")) == 1


def test_mostra_resultado_da_classificacao(usar_cliente):
    usar_cliente()
    app = _abrir_sessao(_novo_app(), "Qualifying")

    assert not app.exception
    tabela = app.dataframe[0].value
    assert tabela.iloc[0]["Tempo"] == "1:30.984"
    (grafico,) = app.get("plotly_chart")
    titulo = json.loads(grafico.proto.spec)["layout"]["title"]["text"]
    assert "última fase disputada" in titulo


def test_trocar_gp_nao_mantem_sessao_do_gp_anterior(usar_cliente, api_falsa, dados_api):
    """Sessões com o mesmo nome em GPs diferentes não podem se misturar."""
    sessoes_japao = [
        {**s, "session_key": s["session_key"] + 1000, "meeting_key": 1220}
        for s in dados_api("sessions_1219.json")
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.params.get("meeting_key") == "1220":
            return httpx.Response(200, json=sessoes_japao)
        return api_falsa(request)

    usar_cliente(handler)
    app = _abrir_sessao(_novo_app(), "Race")
    _selecionar(app, "GP", "Japanese Grand Prix")

    sessao = next(s for s in app.sidebar.selectbox if s.label == "Sessão").value
    assert sessao.meeting_key == 1220
    assert app.subheader[0].value == "Japanese Grand Prix — Practice 1"


def test_sessao_sem_resultado_mostra_aviso(usar_cliente):
    usar_cliente()
    app = _abrir_sessao(_novo_app(), "Practice 1")

    assert not app.exception
    assert "ainda não está disponível" in app.info[0].value
    assert not app.dataframe


def test_erro_da_api_e_exibido(usar_cliente):
    usar_cliente(lambda request: httpx.Response(500, text="erro interno"))
    app = _novo_app().run()

    assert not app.exception
    assert "Não foi possível carregar os GPs" in app.sidebar.error[0].value


def test_erro_ao_carregar_resultado_e_exibido(usar_cliente, api_falsa):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/session_result"):
            return httpx.Response(503)
        return api_falsa(request)

    usar_cliente(handler)
    app = _abrir_sessao(_novo_app(), "Race")

    assert not app.exception
    assert "Não foi possível carregar o resultado" in app.error[0].value
    assert not app.dataframe
