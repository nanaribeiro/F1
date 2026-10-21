# Instalação

O projeto usa **pyenv** para a versão do Python e **Poetry** para dependências
e ambiente virtual. Não use `pip install`, `venv` ou `virtualenv`.

## Pré-requisitos

- [pyenv](https://github.com/pyenv/pyenv) (no Windows,
  [pyenv-win](https://github.com/pyenv-win/pyenv-win), com os mesmos comandos).
- [Poetry](https://python-poetry.org/docs/#installation) 2.x.

## 1. Python com pyenv

A versão oficial está em `.python-version` (atualmente **3.12.10**), compatível
com `requires-python = ">=3.12,<4.0"` do `pyproject.toml`.

```bash
pyenv install 3.12.10
pyenv local 3.12.10      # já definido no .python-version
python --version         # Python 3.12.10
```

!!! tip "pyenv-win sem a versão 3.12 na lista"
    Se `pyenv install --list` não mostrar versões 3.12, o cache de versões do
    pyenv-win está desatualizado. Rode `pyenv update`. Se ele falhar no
    Windows 11 (erro do `htmlfile`), atualize o pyenv-win ou adicione a versão
    manualmente ao arquivo `%USERPROFILE%\.pyenv\pyenv-win\.versions_cache.xml`.

## 2. Ambiente virtual com Poetry

O ambiente fica em `.venv`, na raiz do projeto (configurado em `poetry.toml`).

```bash
poetry config virtualenvs.in-project true --local
poetry env use "$(pyenv which python)"
poetry install
```

Confira o ambiente:

```bash
poetry env info --path       # deve terminar em .venv dentro do projeto
poetry run python --version  # deve coincidir com .python-version
```

!!! warning "Variável `VIRTUAL_ENV` já definida"
    Se o terminal já tiver uma variável `VIRTUAL_ENV` apontando para outro
    Python (por exemplo, ativada pelo editor), o Poetry usa esse interpretador
    e recusa a versão do projeto. Desative-a antes (`deactivate`, ou
    `unset VIRTUAL_ENV` no bash, ou `Remove-Item Env:VIRTUAL_ENV` no
    PowerShell).

## Grupos de dependências

| Grupo | Pacotes |
|---|---|
| principal | `httpx`, `streamlit`, `plotly`, `pandas` |
| `dev` | `ruff`, `taskipy` |
| `test` | `pytest`, `pytest-cov` |
| `docs` | `mkdocs`, `mkdocs-material` |

`poetry install` instala todos os grupos. Para adicionar dependências use
`poetry add <pacote>` (ou `poetry add --group <grupo> <pacote>`) e faça commit
de `pyproject.toml` e `poetry.lock` juntos.

## Recriar o ambiente

```bash
poetry env remove --all
rm -rf .venv
poetry env use "$(pyenv which python)"
poetry install
```
