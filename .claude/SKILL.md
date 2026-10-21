---
name: projeto-python-padroes
description: Padrões obrigatórios de desenvolvimento, qualidade, testes e documentação do projeto Python (Poetry, pyenv, Ruff, pytest com cobertura mínima de 50%, MkDocs Material). Use sempre que for criar, alterar, testar, documentar ou configurar o ambiente deste repositório, instalar ou remover dependências, rodar lint, formatação, testes ou build da documentação, mesmo que a tarefa não mencione essas ferramentas explicitamente.
---

# Guia de desenvolvimento do projeto Python

Este documento é a referência oficial para desenvolvedores e agentes de IA que trabalham neste repositório. As regras marcadas como **OBRIGATÓRIO** não podem ser flexibilizadas. Itens marcados como **RECOMENDADO** são opcionais e complementam, sem substituir, os obrigatórios.

> **Convenção de nomes:** `projeto` neste documento é um nome de referência para o pacote localizado em `src/projeto`. Substitua pelo nome real do pacote ao aplicar os exemplos. Os números de versão (por exemplo, Python `3.12`) também são exemplos e devem ser confirmados.

## Sumário

1. [Antes de começar: inspecione o repositório](#1-antes-de-começar-inspecione-o-repositório)
2. [Ferramentas oficiais](#2-ferramentas-oficiais)
3. [Versão do Python com pyenv](#3-versão-do-python-com-pyenv)
4. [Dependências e ambiente virtual com Poetry](#4-dependências-e-ambiente-virtual-com-poetry)
5. [Qualidade de código com Ruff](#5-qualidade-de-código-com-ruff)
6. [Testes com pytest e cobertura](#6-testes-com-pytest-e-cobertura)
7. [Documentação com MkDocs Material](#7-documentação-com-mkdocs-material)
8. [Estrutura do projeto](#8-estrutura-do-projeto)
9. [Fluxo padrão de desenvolvimento](#9-fluxo-padrão-de-desenvolvimento)
10. [Automação local e CI](#10-automação-local-e-ci)
11. [Checklist de conclusão](#11-checklist-de-conclusão)
12. [Proibições](#12-proibições)

---

## 1. Antes de começar: inspecione o repositório

**OBRIGATÓRIO:** não presuma que arquivos ou configurações existem. Antes de propor ou fazer qualquer alteração:

```bash
ls -la
cat .python-version 2>/dev/null
cat pyproject.toml 2>/dev/null
cat mkdocs.yml 2>/dev/null
ls src tests docs 2>/dev/null
git status --short
```

Regras:

- Preserve configurações existentes que já estejam corretas e compatíveis com este guia.
- Se encontrar incompatibilidades (por exemplo, `requirements.txt` paralelo ao Poetry, `black` ou `flake8` configurados, `.venv` fora do padrão, cobertura abaixo de 50%), **relate-as** ao usuário e proponha a correção. Não faça refatorações amplas sem pedido explícito.
- Não invente módulos, funcionalidades de negócio ou requisitos que não foram fornecidos.

## 2. Ferramentas oficiais

| Finalidade | Ferramenta | Configuração central |
|---|---|---|
| Versão do Python | pyenv | `.python-version` |
| Dependências, venv e empacotamento | Poetry | `pyproject.toml` + `poetry.lock` |
| Lint e formatação | Ruff | `pyproject.toml` |
| Testes e cobertura | pytest + pytest-cov | `pyproject.toml` |
| Documentação | MkDocs + Material for MkDocs | `mkdocs.yml` |

**OBRIGATÓRIO:** não substitua nenhuma dessas ferramentas por equivalentes (pip puro, venv, virtualenv, Black, isort, flake8, unittest, Sphinx etc.).

## 3. Versão do Python com pyenv

**OBRIGATÓRIO:**

- A versão oficial do Python é definida no arquivo `.python-version`, versionado no Git.
- A versão em `.python-version` deve ser compatível com a restrição `requires-python` do `pyproject.toml`.
- Configure o pyenv **antes** de criar o ambiente virtual do Poetry.

```bash
# Listar versões instaladas e disponíveis
pyenv versions
pyenv install --list | grep " 3\.12"

# Instalar a versão necessária (exemplo)
pyenv install 3.12.7

# Selecionar localmente (cria/atualiza .python-version)
pyenv local 3.12.7

# Verificar a versão ativa
python --version
pyenv version
```

Para evitar divergência entre pyenv e o ambiente virtual, aponte o Poetry explicitamente para o interpretador do pyenv:

```bash
poetry env use "$(pyenv which python)"
poetry run python --version   # deve coincidir com .python-version
```

Se as versões divergirem, recrie o ambiente (seção 4.6).

## 4. Dependências e ambiente virtual com Poetry

### 4.1 Regras obrigatórias

- Todas as dependências (execução, desenvolvimento, testes, lint, formatação e documentação) são gerenciadas pelo Poetry.
- `pyproject.toml` é o arquivo central de configuração.
- `poetry.lock` **deve ser versionado** e mantido consistente com o `pyproject.toml`.
- **Não** instale dependências globalmente no sistema.
- **Não** use `pip install` para instalar dependências do projeto.
- **Não** crie ambientes paralelos com `venv` ou `virtualenv`.
- Nenhuma ferramenta (Ruff, pytest, MkDocs e plugins) pode depender de instalação global.
- O ambiente virtual deve ficar em `.venv`, na raiz do projeto.
- Comandos de desenvolvimento são executados com `poetry run ...`.

### 4.2 Configuração inicial

```bash
# Instalar o Poetry (uma única vez por máquina, conforme a documentação oficial)
# https://python-poetry.org/docs/#installation

# Criar o venv dentro do projeto (gera poetry.toml local)
poetry config virtualenvs.in-project true --local

# Instalar todas as dependências, incluindo grupos de desenvolvimento
poetry install
```

Verifique se `poetry.toml` (ou a configuração equivalente) está coerente com o repositório e não versione `.venv/`.

### 4.3 Grupos de dependências

Organize as dependências em grupos. Exemplo para Poetry 2.x (confirme a versão do Poetry em uso e ajuste a sintaxe se necessário):

```toml
[project]
name = "projeto"
version = "0.1.0"
requires-python = ">=3.12,<4.0"
dependencies = [
    # dependências de execução
]

[tool.poetry]
packages = [{ include = "projeto", from = "src" }]

[tool.poetry.group.dev.dependencies]
ruff = "*"

[tool.poetry.group.test.dependencies]
pytest = "*"
pytest-cov = "*"

[tool.poetry.group.docs.dependencies]
mkdocs = "*"
mkdocs-material = "*"

[build-system]
requires = ["poetry-core>=2.0.0,<3.0.0"]
build-backend = "poetry.core.masonry.api"
```

> Substitua `"*"` por restrições de versão adequadas (por exemplo, `^0.6`) ao adicionar os pacotes com `poetry add`, que resolve e grava as versões automaticamente.

### 4.4 Comandos do dia a dia

```bash
# Instalar/sincronizar conforme o poetry.lock
poetry install

# Sincronizar removendo pacotes que não estão no lock
poetry install --sync

# Adicionar dependência de execução
poetry add <pacote>

# Adicionar a um grupo específico
poetry add --group test pytest pytest-cov
poetry add --group dev ruff
poetry add --group docs mkdocs mkdocs-material

# Remover dependência
poetry remove <pacote>
poetry remove --group dev <pacote>

# Atualizar o lock e validar consistência
poetry lock
poetry check --lock

# Executar qualquer ferramenta no ambiente do projeto
poetry run <comando>
```

Sempre faça commit de `pyproject.toml` e `poetry.lock` **juntos**.

### 4.5 Verificar o ambiente ativo

```bash
poetry env info            # versão do Python, caminho do venv
poetry env info --path     # deve terminar em .venv dentro do projeto
poetry run which python    # deve apontar para o .venv do projeto
poetry run python --version
```

### 4.6 Recriar o ambiente

Quando houver divergência de versão do Python, ambiente corrompido ou dependências inconsistentes:

```bash
poetry env remove --all
rm -rf .venv
pyenv local 3.12.7                    # confirme a versão desejada
poetry env use "$(pyenv which python)"
poetry install
```

## 5. Qualidade de código com Ruff

### 5.1 Regras obrigatórias

- Ruff é a única ferramenta de lint e formatação. Não adicione Black, isort, flake8, pylint ou similares quando o Ruff já cobrir a função.
- Configure o Ruff no `pyproject.toml`, com versão-alvo do Python **explícita**.
- O código só é considerado concluído quando passar em `ruff check` e `ruff format --check`.

### 5.2 Configuração de referência

Ajuste `target-version` conforme `.python-version`/`requires-python`:

```toml
[tool.ruff]
target-version = "py312"
line-length = 88
src = ["src", "tests"]

[tool.ruff.lint]
select = [
    "E",   # pycodestyle (erros)
    "W",   # pycodestyle (avisos)
    "F",   # pyflakes (imports não usados, nomes indefinidos etc.)
    "I",   # isort (organização de imports)
    "B",   # flake8-bugbear (erros comuns)
    "UP",  # pyupgrade (sintaxe moderna)
    "N",   # pep8-naming
    "C4",  # flake8-comprehensions
    "SIM", # flake8-simplify
]

[tool.ruff.lint.isort]
known-first-party = ["projeto"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

### 5.3 Comandos

```bash
poetry run ruff check .              # análise estática
poetry run ruff check . --fix        # corrige o que for corrigível automaticamente
poetry run ruff format .             # formata o código
poetry run ruff format --check .     # verifica formatação sem alterar (usado na CI)
```

Ao suprimir uma regra com `# noqa` ou `per-file-ignores`, justifique no próprio código ou no commit. Não desative regras apenas para fazer a verificação passar.

## 6. Testes com pytest e cobertura

### 6.1 Regras obrigatórias

- Framework: **pytest**. Cobertura: **pytest-cov**.
- Cobertura mínima de **50%** sobre o pacote `projeto`, localizado em `src/projeto`.
- A execução dos testes **deve falhar** se a cobertura ficar abaixo de 50%.
- **Não** reduza, desabilite ou contorne a exigência de cobertura (por exemplo, baixar `--cov-fail-under`, excluir arquivos relevantes em `omit`, usar `# pragma: no cover` sem justificativa).
- **Não** crie testes artificiais apenas para subir o percentual. Cada teste deve verificar comportamento real.

### 6.2 Configuração persistida no `pyproject.toml`

```toml
[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
addopts = [
    "--cov=projeto",
    "--cov-report=term-missing",
    "--cov-fail-under=50",
]

[tool.coverage.run]
branch = true

[tool.coverage.report]
show_missing = true
```

Com isso, `poetry run pytest` já aplica a cobertura e o limite mínimo, sem parâmetros manuais. O pacote `projeto` precisa estar instalado no venv (`poetry install`) para que `--cov=projeto` resolva o código em `src/projeto`.

### 6.3 Organização dos testes

- Todos os testes ficam em `tests/`, espelhando a estrutura de `src/projeto`:

```text
src/projeto/servicos/calculo.py   →   tests/servicos/test_calculo.py
```

- Nomes descritivos para arquivos e funções, por exemplo `test_calcular_total_retorna_zero_para_lista_vazia`.
- Testes unitários independentes, determinísticos e reproduzíveis (sem depender de ordem de execução).
- Cubra comportamentos principais, regras de negócio, caminhos alternativos e tratamento de erros (use `pytest.raises`).
- Evite dependência de rede, serviços externos ou estado compartilhado; use `monkeypatch`, `tmp_path`, fixtures e `unittest.mock` quando apropriado.
- Prefira `@pytest.mark.parametrize` para variações do mesmo comportamento.

### 6.4 Comandos

```bash
# Todos os testes (cobertura e limite aplicados via pyproject.toml)
poetry run pytest

# Um arquivo, uma função ou um padrão
poetry run pytest tests/servicos/test_calculo.py
poetry run pytest tests/servicos/test_calculo.py::test_calcular_total_retorna_zero_para_lista_vazia
poetry run pytest -k "calculo and not erro"

# Relatórios de cobertura
poetry run pytest --cov-report=term-missing
poetry run pytest --cov-report=html      # gera htmlcov/
poetry run pytest --cov-report=xml       # gera coverage.xml (útil na CI)
```

Ao executar um teste isolado, o limite de 50% pode falhar por considerar apenas aquele teste. Isso é esperado; a validação oficial de cobertura é feita com a suíte completa (`poetry run pytest`).

## 7. Documentação com MkDocs Material

### 7.1 Regras obrigatórias

- Documentação escrita em **Markdown**, no diretório `docs/`.
- Tema **Material for MkDocs**, configurado em `mkdocs.yml`.
- Dependências no grupo `docs` (ou `dev`) do Poetry.
- Mantenha a documentação **sincronizada** com o código: toda alteração de comportamento, instalação, comandos ou API pública exige atualização dos documentos correspondentes.
- Antes de concluir alterações relevantes, a documentação deve compilar sem erros e sem avisos.

### 7.2 Conteúdo mínimo

- Página inicial (`docs/index.md`) com visão geral, objetivos e funcionalidades do projeto.
- Instalação e configuração do ambiente (pyenv e Poetry).
- Execução do projeto.
- Testes e cobertura.
- Lint e formatação.
- Funcionalidades principais, com exemplos de uso e comandos executáveis quando úteis.
- APIs públicas e módulos relevantes, quando aplicável.

> Descreva apenas o que existe no projeto. Se faltar informação sobre objetivos ou funcionalidades, peça ao usuário em vez de inventar.

### 7.3 Configuração de referência

```yaml
site_name: Projeto
site_description: Documentação técnica do projeto
docs_dir: docs
strict: true

theme:
  name: material
  language: pt-BR
  features:
    - navigation.sections
    - content.code.copy

nav:
  - Início: index.md
  # - Instalação: instalacao.md
  # - Desenvolvimento: desenvolvimento.md
```

Mantenha `nav` alinhado com os arquivos reais de `docs/`.

### 7.4 Comandos

```bash
poetry run mkdocs serve             # servidor local com recarga automática
poetry run mkdocs build --strict    # build; falha em qualquer aviso (obrigatório antes de concluir)
```

**RECOMENDADO:** se for necessário gerar documentação de API a partir de docstrings, adicione `mkdocstrings[python]` ao grupo `docs` e valide com `mkdocs build --strict`.

## 8. Estrutura do projeto

Adote o layout `src/`. Estrutura de referência:

```text
.
├── .python-version
├── .gitignore
├── .pre-commit-config.yaml   # opcional, se adotado
├── pyproject.toml
├── poetry.lock
├── mkdocs.yml
├── README.md
├── SKILL.md
├── src/
│   └── projeto/
│       ├── __init__.py
│       └── ...
├── tests/
│   └── ...
└── docs/
    ├── index.md
    └── ...
```

- Altere essa estrutura somente com justificativa técnica clara, registrada na documentação.
- Não versione arquivos gerados. O `.gitignore` deve cobrir, no mínimo: `.venv/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `.coverage`, `htmlcov/`, `coverage.xml`, `site/` e `dist/`.

## 9. Fluxo padrão de desenvolvimento

**OBRIGATÓRIO** para toda nova funcionalidade ou correção:

1. **Verificar o Python:** `pyenv version` e `poetry run python --version`.
2. **Sincronizar dependências:** `poetry install`.
3. **Implementar** seguindo as convenções do projeto (código em `src/projeto`).
4. **Testes:** criar ou atualizar os testes unitários correspondentes em `tests/`.
5. **Ruff:**

   ```bash
   poetry run ruff check . --fix
   poetry run ruff format .
   poetry run ruff check .
   poetry run ruff format --check .
   ```

6. **Testes com cobertura (mínimo de 50%):** `poetry run pytest`.
7. **Documentação:** atualizar `docs/` e rodar `poetry run mkdocs build --strict`.
8. **Revisar as alterações:** `git status` e `git diff`. Confirme que não há dependências instaladas fora do venv, nem arquivos gerados versionados indevidamente (`.venv`, `htmlcov`, `site`, caches), e que `pyproject.toml` e `poetry.lock` estão consistentes (`poetry check --lock`).

## 10. Automação local e CI

As verificações automatizadas devem usar os comandos e ferramentas do ambiente virtual do projeto (`poetry run ...`) e validar:

| Verificação | Comando |
|---|---|
| Versão do Python compatível | `poetry run python --version` (confere com `.python-version` e `requires-python`) |
| Dependências consistentes | `poetry check --lock` |
| Sem erros de lint | `poetry run ruff check .` |
| Formatação conforme o Ruff | `poetry run ruff format --check .` |
| Testes aprovados | `poetry run pytest` |
| Cobertura mínima de 50% em `src/projeto` | já aplicada pelo `pytest` via `--cov-fail-under=50` |
| Documentação compila sem erros | `poetry run mkdocs build --strict` |

### 10.1 Exemplo de pipeline (GitHub Actions)

Adapte à plataforma de CI efetivamente usada pelo projeto; este exemplo é apenas referência:

```yaml
name: CI
on: [push, pull_request]

jobs:
  qualidade:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version-file: .python-version
      - run: pipx install poetry
      - run: poetry config virtualenvs.in-project true --local
      - run: poetry install
      - run: poetry check --lock
      - run: poetry run ruff check .
      - run: poetry run ruff format --check .
      - run: poetry run pytest
      - run: poetry run mkdocs build --strict
```

### 10.2 pre-commit (RECOMENDADO)

Se adotado, o `pre-commit` **complementa** as verificações obrigatórias e não as substitui. Use hooks locais que chamem o ambiente do Poetry:

```yaml
repos:
  - repo: local
    hooks:
      - id: ruff-check
        name: ruff check
        entry: poetry run ruff check
        language: system
        types: [python]
      - id: ruff-format
        name: ruff format --check
        entry: poetry run ruff format --check
        language: system
        types: [python]
```

## 11. Checklist de conclusão

Uma tarefa só está concluída quando **todos** os itens abaixo estiverem verdadeiros:

- [ ] `.python-version` compatível com `requires-python`.
- [ ] Dependências adicionadas via Poetry; `pyproject.toml` e `poetry.lock` commitados juntos e consistentes.
- [ ] `poetry run ruff check .` sem erros.
- [ ] `poetry run ruff format --check .` sem pendências.
- [ ] `poetry run pytest` aprovado, com cobertura de `src/projeto` ≥ 50%.
- [ ] Testes novos ou atualizados para o comportamento alterado.
- [ ] `poetry run mkdocs build --strict` sem erros.
- [ ] Documentação atualizada para refletir as mudanças.
- [ ] Nenhum arquivo gerado ou segredo versionado.

## 12. Proibições

- Usar `pip install`, `venv` ou `virtualenv` para o projeto.
- Instalar Ruff, pytest, MkDocs ou plugins globalmente.
- Substituir Poetry, pyenv, Ruff, pytest ou MkDocs Material por outras ferramentas.
- Reduzir, desabilitar ou contornar a cobertura mínima ou regras do Ruff para fazer verificações passarem.
- Criar testes sem valor apenas para aumentar a cobertura.
- Versionar `.venv/`, caches, relatórios de cobertura ou o diretório `site/`.
- Inventar funcionalidades, módulos ou requisitos não fornecidos.
