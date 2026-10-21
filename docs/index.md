# F1 Dashboard

Dashboard web feito com **Streamlit** e **Plotly** para consultar o resultado
de sessões de Fórmula 1 usando a [API OpenF1](https://openf1.org).

## Objetivo

Permitir escolher uma sessão (treino, classificação, sprint ou corrida) de
qualquer GP a partir de 2023 e ver o resultado final com pilotos, equipes,
tempos e diferença para o líder.

## Funcionalidades (v1)

- Seleção encadeada **Ano → GP → Sessão** na barra lateral. GPs cancelados
  não aparecem e GPs e sessões ficam em ordem cronológica.
- Tabela com o resultado final: posição, número, sigla (com a cor da equipe),
  piloto, equipe, tempo, gap para o líder, voltas e status
  (`Classificado`, `DNF`, `DNS` ou `DSQ`).
- Gráfico de barras do gap para o líder, com as cores das equipes.
- Em classificações, tempo e gap exibidos são os da **última fase** (Q1, Q2
  ou Q3) disputada por cada piloto.
- Cache das consultas por 1 hora e mensagens de erro quando a API falha.

Tempos de volta, estratégia de pneus, telemetria e dados em tempo real estão
fora do escopo da v1.

## Fonte de dados

Os dados vêm da [OpenF1](https://openf1.org), uma API open-source com dados
históricos gratuitos a partir de 2023, sem autenticação.

!!! note "Projeto não oficial"
    A OpenF1 não tem vínculo com as empresas da Fórmula 1. Os resultados ficam
    disponíveis na API alguns minutos após a publicação oficial.

## Próximos passos

- [Instalação](instalacao.md) do ambiente com pyenv e Poetry.
- [Uso](uso.md) do dashboard.
- [Desenvolvimento](desenvolvimento.md): lint, testes e documentação.
- [Arquitetura](arquitetura.md): módulos e endpoints usados.
