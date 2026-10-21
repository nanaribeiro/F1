# Desenvolvimento

Todos os comandos rodam no ambiente do projeto com `poetry run`.

## Atalhos (taskipy)

As tarefas mais comuns estão em `[tool.taskipy.tasks]` no `pyproject.toml`:

| Comando | Executa | Uso |
|---|---|---|
| `poetry run task format` | `ruff check . --fix && ruff format .` | Corrige o que for automático e formata |
| `poetry run task lint` | `ruff check . && ruff format --check .` | Verifica sem alterar arquivos |
| `poetry run task test` | `pytest` | Testes com cobertura (mínimo de 50%) |
| `poetry run task docs` | `mkdocs build --strict` | Compila a documentação; falha em avisos |

`poetry run task --list` mostra todas as tarefas. As seções abaixo detalham
cada ferramenta.

## Fluxo para cada alteração

1. Confira o Python: `pyenv version` e `poetry run python --version`.
2. Sincronize as dependências: `poetry install`.
3. Implemente em `src/f1` e crie ou atualize os testes em `tests/`.
4. Rode `poetry run task format`, `task lint`, `task test` e `task docs`.
5. Revise `git status` e `git diff`; confira `poetry check --lock`.

## Lint e formatação (Ruff)

```bash
poetry run ruff check . --fix     # corrige o que for automático
poetry run ruff format .          # formata
poetry run ruff check .           # deve passar sem erros
poetry run ruff format --check .  # deve passar sem pendências
```

A configuração fica em `[tool.ruff]` no `pyproject.toml` (alvo `py312`, linha
de 88 caracteres, regras `E, W, F, I, B, UP, N, C4, SIM`).

## Testes e cobertura (pytest)

```bash
poetry run pytest                            # suíte completa + cobertura
poetry run pytest tests/test_services.py     # um arquivo
poetry run pytest -k classificacao           # por nome
poetry run pytest --cov-report=html          # relatório em htmlcov/
```

A cobertura do pacote `f1` é medida automaticamente e o `pytest` **falha se
ficar abaixo de 50%** (`--cov-fail-under=50` no `pyproject.toml`). Ao rodar um
teste isolado, o limite pode falhar; a validação oficial é a suíte completa.

Os testes não acessam a rede:

- `tests/conftest.py` define uma OpenF1 falsa com `httpx.MockTransport`, que
  responde com as fixtures de `tests/fixtures/` (dados reais do GP de
  Singapura de 2023, recortados) e com `404 "No results found."` nas demais
  consultas, como a API real.
- `tests/dashboard/test_app.py` executa o app com
  `streamlit.testing.v1.AppTest`, trocando o cliente pela OpenF1 falsa.

| Arquivo de teste | Cobre |
|---|---|
| `tests/test_client.py` | Query string com operadores e valores repetidos, conversão das respostas, novas tentativas em 429, erros HTTP, de rede e de JSON |
| `tests/test_models.py` | `from_api` com campos extras, ausentes e obrigatórios |
| `tests/test_services.py` | Ordenação, formatação de tempo, fases da classificação, retardatários, DNF/DNS/DSQ, piloto ausente |
| `tests/dashboard/test_app.py` | Renderização do app, troca de GP sem misturar sessões, avisos e erros |

## Documentação (MkDocs Material)

```bash
poetry run mkdocs serve           # http://127.0.0.1:8000 com recarga automática
poetry run mkdocs build --strict  # obrigatório antes de concluir: falha em avisos
```

As páginas ficam em `docs/` e o menu em `nav` no `mkdocs.yml`. Atualize a
documentação sempre que mudar comportamento, comandos ou API pública.

## Automação

- **CI**: `.github/workflows/ci.yml` roda `poetry check --lock`, Ruff, pytest e
  `mkdocs build --strict` a cada push e pull request.
- **pre-commit** (opcional): `.pre-commit-config.yaml` tem hooks locais de
  `ruff check` e `ruff format --check` via Poetry. Para ativar, instale o
  [pre-commit](https://pre-commit.com) fora do projeto (por exemplo, com
  `pipx install pre-commit`) e rode `pre-commit install`.
