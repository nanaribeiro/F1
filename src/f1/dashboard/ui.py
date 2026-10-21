"""Interface Streamlit com o resultado das sessões de F1 (dados da OpenF1).

Esta camada só cuida da interface; consultas ficam em ``f1.client`` e as
regras de montagem da tabela em ``f1.services``. O script executado pelo
Streamlit é ``f1/dashboard/app.py``, que apenas chama :func:`main`.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from pandas.io.formats.style import Styler

from f1.client import OpenF1Client, OpenF1Error
from f1.models import Driver, Meeting, Session, SessionResult
from f1.services import (
    cor_texto_contraste,
    montar_classificacao,
    ordenar_meetings,
    ordenar_sessoes,
)

PRIMEIRO_ANO = 2023  # início dos dados históricos gratuitos da OpenF1
TTL_SEGUNDOS = 3600


@st.cache_resource
def obter_cliente() -> OpenF1Client:
    return OpenF1Client()


@st.cache_data(ttl=TTL_SEGUNDOS, show_spinner="Carregando GPs...")
def carregar_meetings(ano: int) -> list[Meeting]:
    return ordenar_meetings(obter_cliente().meetings(ano))


@st.cache_data(ttl=TTL_SEGUNDOS, show_spinner="Carregando sessões...")
def carregar_sessoes(meeting_key: int) -> list[Session]:
    return ordenar_sessoes(obter_cliente().sessions(meeting_key))


@st.cache_data(ttl=TTL_SEGUNDOS, show_spinner="Carregando resultado...")
def carregar_resultado(session_key: int) -> tuple[list[SessionResult], list[Driver]]:
    cliente = obter_cliente()
    return cliente.session_result(session_key), cliente.drivers(session_key)


def _colorir_sigla(tabela: pd.DataFrame) -> Styler:
    """Pinta a coluna ``Sigla`` com a cor da equipe."""
    cores = tabela["Cor"]

    def estilo(coluna: pd.Series) -> list[str]:
        if coluna.name != "Sigla":
            return [""] * len(coluna)
        return [
            f"background-color: {cor}; color: {cor_texto_contraste(cor)}"
            for cor in cores
        ]

    exibida = tabela.drop(columns=["Cor", "Gap (s)"])
    return exibida.style.apply(estilo)


def _grafico_gap(tabela: pd.DataFrame, classificacao: bool) -> go.Figure:
    dados = tabela.dropna(subset=["Gap (s)"])
    figura = go.Figure(
        go.Bar(
            x=dados["Sigla"],
            y=dados["Gap (s)"],
            marker_color=list(dados["Cor"]),
            customdata=dados[["Piloto", "Equipe"]],
            hovertemplate=(
                "%{customdata[0]} (%{customdata[1]})<br>+%{y:.3f} s<extra></extra>"
            ),
        )
    )
    titulo = "Gap para o líder (s)"
    if classificacao:
        titulo += " — última fase disputada por cada piloto"
    figura.update_layout(title=titulo, xaxis_title=None, yaxis_title="segundos")
    return figura


def main() -> None:
    st.set_page_config(page_title="F1 Dashboard", page_icon="🏎️", layout="wide")
    st.title("Resultados da Fórmula 1")
    st.caption("Dados: [OpenF1](https://openf1.org) — projeto não oficial.")

    with st.sidebar:
        st.header("Filtros")
        anos = list(range(date.today().year, PRIMEIRO_ANO - 1, -1))
        ano = st.selectbox("Ano", anos)

        try:
            meetings = carregar_meetings(ano)
        except OpenF1Error as erro:
            st.error(f"Não foi possível carregar os GPs: {erro}")
            st.stop()
        if not meetings:
            st.info(f"Nenhum GP encontrado para {ano}.")
            st.stop()
        # A ``key`` depende da escolha anterior: sem ela, o Streamlit mantém o
        # item antigo quando os rótulos coincidem (ex.: "Day 1" em anos
        # diferentes) e o dashboard mostraria dados de outro GP.
        meeting = st.selectbox(
            "GP", meetings, format_func=lambda m: m.meeting_name, key=f"gp_{ano}"
        )

        try:
            sessoes = carregar_sessoes(meeting.meeting_key)
        except OpenF1Error as erro:
            st.error(f"Não foi possível carregar as sessões: {erro}")
            st.stop()
        if not sessoes:
            st.info("Nenhuma sessão encontrada para este GP.")
            st.stop()
        sessao = st.selectbox(
            "Sessão",
            sessoes,
            format_func=lambda s: s.session_name,
            key=f"sessao_{meeting.meeting_key}",
        )

    st.subheader(f"{meeting.meeting_name} — {sessao.session_name}")

    try:
        resultados, pilotos = carregar_resultado(sessao.session_key)
    except OpenF1Error as erro:
        st.error(f"Não foi possível carregar o resultado: {erro}")
        st.stop()

    tabela = montar_classificacao(resultados, pilotos)
    if tabela.empty:
        st.info("O resultado desta sessão ainda não está disponível.")
        return

    st.dataframe(_colorir_sigla(tabela), hide_index=True)
    st.plotly_chart(_grafico_gap(tabela, sessao.is_qualifying))
