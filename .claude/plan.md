# plan.md — Dashboard F1 com a API OpenF1

## Contexto

O repositório `F1` tem apenas um esqueleto: `src/f1/__init__.py`, `tests/__init__.py` e um `pyproject.toml` mínimo (pacote `f1`, layout `src/`, Poetry 2.x). O objetivo é criar um **dashboard (Streamlit + Plotly)** que consome a **API OpenF1** (`https://api.openf1.org/v1`, dados históricos 2023+, sem autenticação), seguindo os padrões do `SKILL.md`: pyenv, Poetry, Ruff, pytest com cobertura ≥ 50% e MkDocs Material.

**Escopo da v1:** seletor **Ano → GP → Sessão** e exibição do **resultado final** da sessão com os pilotos e equipes. Endpoints usados: `/meetings`, `/sessions`, `/session_result`, `/drivers`. Tempos de volta, pneus e telemetria ficam fora da v1.

### Incompatibilidades encontradas (a corrigir)

| Item | Situação atual | Correção |
|---|---|---|
| `.python-version` | `3.11.0b4` (**beta**) | 3.12.x estável mais recente (via `pyenv install --list`) |
| `requires-python` | `>=3.11` (sem limite superior) | `>=3.12,<4.0` |
| Ferramentas | Ruff, pytest, MkDocs ausentes | adicionar via `poetry add --group ...` |
| `poetry.lock` | inexistente | gerar com `poetry lock` e versionar |
| `.gitignore`, `mkdocs.yml`, `docs/` | inexistentes | criar |
| `poetry.toml` | inexistente | `poetry config virtualenvs.in-project true --local` |

## Etapas

### 1. Ambiente (pyenv + Poetry)
Windows usa **pyenv-win** (mesmos comandos).
```bash
pyenv install --list | grep " 3\.12"     # escolher a 3.12.x mais recente
pyenv install 3.12.<x>
pyenv local 3.12.<x>                       # atualiza .python-version
poetry config virtualenvs.in-project true --local
poetry env use "$(pyenv which python)"
```
Ajustar `requires-python = ">=3.12,<4.0"` no `pyproject.toml`.

### 2. Dependências
```bash
poetry add httpx streamlit plotly pandas
poetry add --group dev ruff
poetry add --group test pytest pytest-cov
poetry add --group docs mkdocs mkdocs-material
poetry install
poetry check --lock
```
Testes HTTP usam `httpx.MockTransport` (sem dependência extra, sem rede).

### 3. Configuração no `pyproject.toml`
- `[tool.ruff]` com `target-version = "py312"`, `line-length = 88`, `src = ["src", "tests"]`, regras `E, W, F, I, B, UP, N, C4, SIM`, `known-first-party = ["f1"]`, formato com aspas duplas (referência da seção 5.2 do SKILL.md).
- `[tool.pytest.ini_options]` com `testpaths = ["tests"]` e `addopts = ["--cov=f1", "--cov-report=term-missing", "--cov-fail-under=50"]`.
- `[tool.coverage.run] branch = true` e `[tool.coverage.report] show_missing = true`.

### 4. Estrutura do código

```text
src/f1/
├── __init__.py
├── client.py          # cliente HTTP da OpenF1
├── models.py          # dataclasses de domínio
├── services.py        # regras de montagem da classificação (lógica pura)
└── dashboard/
    ├── __init__.py
    └── app.py         # app Streamlit (camada fina)
```

**`client.py` — `OpenF1Client`**
- Recebe `base_url` (padrão `https://api.openf1.org/v1`), `timeout` e um `httpx.Client` opcional (injeção para testes).
- `_get(endpoint, filtros)`: monta a query string **manualmente** para suportar operadores (`>=`, `<=`, `>`, `<`) e valores repetidos, conforme a seção 3 da doc da API; retorna a lista JSON.
- Métodos: `meetings(year)`, `sessions(meeting_key)`, `session_result(session_key)`, `drivers(session_key)`.
- Erros HTTP/rede/JSON inválido viram `OpenF1Error` (exceção própria).

**`models.py`** — dataclasses imutáveis (`frozen=True`) `Meeting`, `Session`, `Driver`, `SessionResult`, com `from_api(dict)` que ignora campos desconhecidos e não usa os deprecados (`country_code`).

**`services.py`** — funções puras, sem rede:
- `ordenar_meetings(...)`: remove cancelados (`is_cancelled`) e ordena por `date_start`.
- `montar_classificacao(resultados, pilotos) -> pandas.DataFrame`: junta `session_result` com `drivers` por `driver_number` e produz colunas Posição, Piloto (sigla/nome), Equipe, Cor da equipe, Tempo, Gap, Voltas, Status.
- Tratar casos da doc: em **classificação** `duration`/`gap_to_leader` são arrays [Q1, Q2, Q3] (exibir melhor fase disponível); `gap_to_leader` pode ser `"+N LAP(S)"`; `dnf`/`dns`/`dsq` → Status; `position` nula vai para o fim.
- `formatar_tempo(segundos)` → `m:ss.mmm`.

**`dashboard/app.py`** — apenas UI:
- Sidebar: `selectbox` de ano (2023 até o ano atual), GP e sessão.
- Chamadas ao cliente envolvidas em `st.cache_data` (TTL), erros exibidos com `st.error`.
- Tabela da classificação (`st.dataframe`) e um gráfico Plotly de barras do gap para o líder, colorido por `team_colour`.
- Execução: `poetry run streamlit run src/f1/dashboard/app.py` (imports absolutos `from f1...`).

### 5. Testes (`tests/` espelhando `src/f1`)
- `tests/test_client.py`: montagem de URL com operadores e valores repetidos; parsing de resposta; `OpenF1Error` em status 4xx/5xx, timeout e JSON inválido — tudo via `httpx.MockTransport`.
- `tests/test_models.py`: `from_api` com campos extras/ausentes.
- `tests/test_services.py`: `@pytest.mark.parametrize` para corrida vs. classificação, retardatários (`+1 LAP`), DNF/DNS/DSQ, piloto sem dados em `/drivers`, meetings cancelados, `formatar_tempo`.
- `tests/dashboard/test_app.py`: smoke test com `streamlit.testing.v1.AppTest` e cliente mockado (renderiza sem exceção e mostra a tabela).
- Fixtures JSON pequenas em `tests/fixtures/`, baseadas nos formatos da doc.

### 6. Documentação (MkDocs Material, `strict: true`, `language: pt-BR`)
```text
docs/
├── index.md            # visão geral, objetivo, funcionalidades da v1, fonte de dados (OpenF1, não oficial)
├── instalacao.md       # pyenv + Poetry
├── uso.md              # como rodar o dashboard, fluxo Ano → GP → Sessão
├── desenvolvimento.md  # Ruff, pytest/cobertura, build da doc
└── arquitetura.md      # módulos client/models/services/dashboard e endpoints usados
```
`nav` do `mkdocs.yml` alinhado com esses arquivos. Atualizar o `README.md` com resumo e link para a doc.

### 7. Arquivos de repositório
- `.gitignore`: `.venv/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `.coverage`, `htmlcov/`, `coverage.xml`, `site/`, `dist/`, `.streamlit/secrets.toml`.
- Versionar `pyproject.toml` e `poetry.lock` juntos.
- Opcional (RECOMENDADO): `.github/workflows/ci.yml` e `.pre-commit-config.yaml` conforme seção 10 do SKILL.md.

## Verificação (checklist do SKILL.md)

```bash
pyenv version && poetry run python --version   # 3.12.x, igual ao .python-version
poetry check --lock
poetry run ruff check . --fix && poetry run ruff format .
poetry run ruff check .
poetry run ruff format --check .
poetry run pytest                              # falha se cobertura de f1 < 50%
poetry run mkdocs build --strict
git status && git diff                         # sem .venv, caches, site/ ou htmlcov/
```
Teste manual: `poetry run streamlit run src/f1/dashboard/app.py`, selecionar **2023 → Singapore → Race** e conferir que o resultado mostra Sainz (55) em 1º, Norris e Hamilton em seguida, com cores das equipes.

## Fora do escopo da v1
Tempos de volta (`/laps`), estratégia de pneus (`/stints`, `/pit`), telemetria (`/car_data`), dados em tempo real (exigem assinatura).
