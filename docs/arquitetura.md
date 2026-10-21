# Arquitetura

```text
src/f1/
├── __init__.py
├── client.py          # cliente HTTP da OpenF1
├── models.py          # dataclasses de domínio
├── services.py        # montagem da classificação (lógica pura)
└── dashboard/
    ├── __init__.py
    ├── app.py         # ponto de entrada do Streamlit
    └── ui.py          # interface Streamlit
```

O fluxo é `ui` → `client` (rede) → `models` → `services` (tabela) → `ui`.
Somente `client.py` acessa a rede, e só `dashboard/` depende do Streamlit.

## `f1.client`

`OpenF1Client(base_url=BASE_URL, timeout=10.0, http_client=None,
tentativas=3, esperar=time.sleep)` consulta a API. O `http_client` opcional
permite injetar um `httpx.Client` (nos testes, com `httpx.MockTransport`), e
`esperar` permite substituir a pausa entre tentativas.

| Método | Endpoint | Retorno |
|---|---|---|
| `meetings(year)` | `/meetings?year=` | `list[Meeting]` |
| `sessions(meeting_key)` | `/sessions?meeting_key=` | `list[Session]` |
| `session_result(session_key)` | `/session_result?session_key=` | `list[SessionResult]` |
| `drivers(session_key)` | `/drivers?session_key=` | `list[Driver]` |

A query string é montada por `montar_query(filtros)`, que aceita operadores no
nome do filtro e listas para valores repetidos:

```python
from f1.client import OpenF1Client, montar_query

montar_query({"position<=": 3, "driver_number": [4, 81]})
# 'position<=3&driver_number=4&driver_number=81'

cliente = OpenF1Client()
resultado = cliente.session_result(9165)  # Singapura 2023, corrida
```

Tratamento de respostas:

- `404` com `{"detail": "No results found."}` (como a API responde a consultas
  vazias) vira lista vazia.
- `429` (a API aceita no máximo 3 requisições por segundo) é repetido até
  `tentativas` vezes, esperando o `Retry-After` em segundos, se houver, ou 1 s,
  2 s... conforme a tentativa. Se o limite persistir, vira `OpenF1Error`.
- Outros status de erro, falhas de rede/timeout, JSON inválido ou resposta que
  não seja uma lista viram `OpenF1Error`.

## `f1.models`

Dataclasses imutáveis (`frozen=True`): `Meeting`, `Session`, `Driver` e
`SessionResult`. Cada uma tem `from_api(dict)`, que lê só os campos usados,
ignora os desconhecidos e os deprecados (como `country_code`) e exige os
campos de identificação (`KeyError` se faltarem). Datas viram `datetime`.

Em `SessionResult`, `duration` e `gap_to_leader` mantêm o formato da API:
número, texto `"+N LAP(S)"`, lista `[Q1, Q2, Q3]` (classificação) ou `None`.

## `f1.services`

Funções puras, sem rede:

| Função | Descrição |
|---|---|
| `ordenar_meetings(meetings)` / `ordenar_sessoes(sessoes)` | Removem cancelados e ordenam por `date_start` |
| `montar_classificacao(resultados, pilotos)` | `DataFrame` com o resultado, juntando por `driver_number` |
| `melhor_fase(resultado)` | `(tempo, gap)` a exibir; em classificação, a última fase com tempo |
| `status(resultado)` | `DSQ`, `DNS`, `DNF` ou `Classificado` |
| `formatar_tempo(segundos)` | `m:ss.mmm`, ou `h:mm:ss.mmm` a partir de 1 hora |
| `cor_texto_contraste(cor)` | Texto preto ou branco legível sobre a cor da equipe |

Colunas de `montar_classificacao`: `Posição`, `Número`, `Sigla`, `Piloto`,
`Equipe`, `Cor`, `Tempo`, `Gap`, `Gap (s)`, `Voltas`, `Status`. `Cor`
(`#RRGGBB`) e `Gap (s)` (numérico) alimentam o estilo e o gráfico e não
aparecem na tabela exibida.

## `f1.dashboard`

- `ui.py` contém a interface (`main()`), as consultas com `st.cache_data`
  (TTL de 1 hora) e o gráfico Plotly. Os seletores de GP e sessão usam uma
  `key` derivada da escolha anterior (`gp_<ano>`, `sessao_<meeting_key>`).
  Assim eles voltam para a primeira opção quando o ano ou o GP muda, e o
  Streamlit não reaproveita uma sessão de outro GP com o mesmo nome.
- `app.py` só importa e chama `ui.main()`.

!!! info "Por que separar `app.py` de `ui.py`?"
    O Streamlit executa `app.py` como script solto, fora do pacote `f1`, e a
    cobertura (`--cov=f1`) não o reconhece como parte do pacote. Com a
    interface em `f1.dashboard.ui`, importada normalmente, ela é medida e
    testada como o restante do código.
