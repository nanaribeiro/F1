# Uso

## Executar o dashboard

```bash
poetry run streamlit run src/f1/dashboard/app.py
```

O Streamlit abre o navegador em `http://localhost:8501`. É preciso acesso à
internet para consultar a API OpenF1.

## Fluxo Ano → GP → Sessão

1. Na barra lateral, escolha o **Ano** (de 2023 até o ano atual).
2. Escolha o **GP**. A lista mostra os GPs e testes do ano em ordem
   cronológica, sem os cancelados.
3. Escolha a **Sessão** (`Practice 1`, `Qualifying`, `Sprint`, `Race`...).

O resultado aparece na área principal:

- **Tabela** com posição, número, sigla (colorida com a cor da equipe), piloto,
  equipe, tempo, gap, voltas e status.
- **Gráfico** de barras com o gap para o líder, em segundos.

Exemplo: **2023 → Singapore Grand Prix → Race** mostra Carlos Sainz (55) em 1º,
seguido de Lando Norris e Lewis Hamilton.

## Como ler a tabela

| Coluna | Significado |
|---|---|
| Posição | Posição final; vazia para quem não foi classificado. Esses pilotos ficam no fim da tabela. |
| Tempo | Corrida: tempo total (`h:mm:ss.mmm`). Treino e classificação: melhor volta (`m:ss.mmm`). |
| Gap | `Líder` para o 1º; `+s.mmm` em segundos; `+N LAP(S)` para retardatários; vazio se não houver dado. |
| Status | `Classificado`, `DNF` (não terminou), `DNS` (não largou) ou `DSQ` (desclassificado). |

Em **classificações**, a API devolve tempos de Q1, Q2 e Q3. O dashboard mostra
o tempo e o gap da última fase em que o piloto marcou volta; por isso, no
gráfico, o gap de um eliminado no Q1 se refere ao líder do Q1.

Pilotos que finalizam sem gap numérico (abandonos ou voltas de atraso) não
aparecem no gráfico, apenas na tabela.

## Mensagens

- **"O resultado desta sessão ainda não está disponível."**: a API ainda não
  publicou o resultado (sessões futuras ou recém-encerradas).
- **"Não foi possível carregar..."**: falha de rede ou erro da API. Quando a
  API recusa por excesso de requisições (máximo de 3 por segundo), o
  dashboard espera e tenta de novo automaticamente; a mensagem só aparece se
  o limite persistir. Tente novamente em instantes.

As consultas ficam em cache por 1 hora. Para forçar novos dados, use
**Clear cache** no menu do Streamlit.
