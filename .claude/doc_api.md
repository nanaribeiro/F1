# OpenF1 API — Documentação

API open-source com dados de telemetria, cronometragem e sessões da Fórmula 1, em JSON ou CSV.

- **Site / docs:** https://openf1.org/docs
- **Base URL:** `https://api.openf1.org/v1`
- **Repositório:** https://github.com/br-g/openf1
- **Dados históricos (a partir de 2023):** gratuitos, sem autenticação
- **Dados em tempo real:** exigem assinatura paga
- Projeto não oficial, sem vínculo com as empresas da Fórmula 1.

---

## 1. Como usar

Toda consulta é um `GET` no formato:

```
https://api.openf1.org/v1/<endpoint>?<filtro1>=<valor>&<filtro2>=<valor>
```

Exemplo (curl):

```bash
curl "https://api.openf1.org/v1/car_data?driver_number=55&session_key=9159&speed>=315"
```

Exemplo (Python):

```python
from urllib.request import urlopen
import json

url = "https://api.openf1.org/v1/car_data?driver_number=55&session_key=9159&speed>=315"
data = json.loads(urlopen(url).read().decode("utf-8"))
print(data)

# Opcional: DataFrame
# import pandas as pd
# df = pd.DataFrame(data)
```

Exemplo (JavaScript):

```javascript
fetch("https://api.openf1.org/v1/car_data?driver_number=55&session_key=9159&speed>=315")
  .then((r) => r.json())
  .then((json) => console.log(json));
```

---

## 2. Conceitos e chaves comuns

| Campo | Descrição |
|---|---|
| `meeting_key` | Identificador do *meeting* (fim de semana de GP ou testes). Aceita `latest` para o mais recente/atual. |
| `session_key` | Identificador da *session* (treino, classificação, sprint, corrida). Aceita `latest`. |
| `driver_number` | Número do piloto na temporada. |
| `date` | Data/hora UTC em ISO 8601. |

**Hierarquia:** `meeting` (GP) → `session` (treino, quali, corrida) → dados da sessão (voltas, pits, telemetria etc.).

Fluxo típico: descubra o `meeting_key` em `/meetings`, o `session_key` em `/sessions`, e então consulte os demais endpoints.

---

## 3. Filtros

- Qualquer atributo pode ser filtro, **exceto arrays**.
- Operadores suportados na URL: `=`, `>`, `>=`, `<`, `<=`.
- Parâmetros repetidos permitem vários valores (ex.: `driver_number=4&driver_number=81`).

**Exemplo:** voltas de saída de box do piloto 55 com pelo menos 2 minutos:

```
/laps?session_key=9222&driver_number=55&is_pit_out_lap=true&lap_duration>=120
```

### Filtro por data

```
/sessions?date_start>=2023-09-01&date_end<=2023-09-30
```

Aceita formatos compatíveis com `dateutil.parser.parse`, por exemplo:
`2021-09-10`, `2021-09-10T14:30:20`, `2021-09-10T14:30:20+00:00`, `09/10/2021`, `10 September 2021`, `2021-09-10 14:30:20 UTC`.

---

## 4. Formato CSV

Adicione `csv=true` para receber CSV em vez de JSON:

```
https://api.openf1.org/v1/sessions?year=2023&csv=true
```

---

## 5. Endpoints

| Endpoint | Descrição | Observações |
|---|---|---|
| [`/car_data`](#car_data) | Telemetria do carro | ~3,7 Hz |
| [`/championship_drivers`](#championship_drivers-beta) | Classificação de pilotos | Beta; só corridas |
| [`/championship_teams`](#championship_teams-beta) | Classificação de equipes | Beta; só corridas |
| [`/drivers`](#drivers) | Informações dos pilotos | Por sessão |
| [`/intervals`](#intervals) | Intervalos entre pilotos | Só corridas; ~4 s |
| [`/laps`](#laps) | Dados de cada volta | |
| [`/location`](#location) | Posição (x, y, z) dos carros | ~3,7 Hz |
| [`/meetings`](#meetings) | GPs e testes | Atualizado à meia-noite UTC |
| [`/overtakes`](#overtakes) | Ultrapassagens | Só corridas; pode ser incompleto |
| [`/pit`](#pit) | Passagens pelos boxes | |
| [`/position`](#position) | Posição dos pilotos na sessão | |
| [`/race_control`](#race_control) | Bandeiras, incidentes, safety car | |
| [`/sessions`](#sessions) | Sessões | Atualizado à meia-noite UTC |
| [`/session_result`](#session_result) | Resultado final da sessão | Disponível minutos após o resultado oficial |
| [`/starting_grid`](#starting_grid) | Grid de largada | Disponível minutos após o resultado oficial |
| [`/stints`](#stints) | Stints (períodos contínuos de pista) | |
| [`/team_radio`](#team_radio) | Rádios piloto–equipe | Seleção limitada |
| [`/weather`](#weather) | Clima da pista | Atualizado a cada minuto |

---

### car_data

Telemetria de cada carro, ~3,7 Hz.

```
/car_data?driver_number=55&session_key=9159&speed>=315
```

| Atributo | Descrição |
|---|---|
| `brake` | Freio pressionado (`100`) ou não (`0`) |
| `date` | Data/hora UTC |
| `driver_number` | Número do piloto |
| `drs` | Status do DRS (tabela abaixo) |
| `meeting_key` | Chave do meeting |
| `n_gear` | Marcha (1–8); `0` = neutro |
| `rpm` | Rotações por minuto |
| `session_key` | Chave da sessão |
| `speed` | Velocidade (km/h) |
| `throttle` | % de acelerador |

**Valores de DRS** (fonte: FastF1):

| Valor | Interpretação |
|---|---|
| 0, 1 | DRS desligado |
| 8 | Detectado, elegível ao entrar na zona de ativação |
| 10, 12, 14 | DRS ligado |
| 2, 3, 9 | Desconhecido |

---

### championship_drivers (beta)

Classificação do campeonato de pilotos. Apenas sessões de corrida.

```
/championship_drivers?session_key=9839&driver_number=4&driver_number=81
```

| Atributo | Descrição |
|---|---|
| `driver_number` | Número do piloto |
| `meeting_key`, `session_key` | Chaves |
| `points_start` | Pontos antes da corrida |
| `points_current` | Pontos durante/após a corrida (depende do momento da chamada) |
| `position_start` | Posição antes da corrida |
| `position_current` | Posição durante/após a corrida |

---

### championship_teams (beta)

Classificação do campeonato de construtores. Apenas sessões de corrida.

```
/championship_teams?session_key=9839&team_name=McLaren
```

| Atributo | Descrição |
|---|---|
| `team_name` | Nome da equipe |
| `meeting_key`, `session_key` | Chaves |
| `points_start` / `points_current` | Pontos antes / durante-após a corrida |
| `position_start` / `position_current` | Posição antes / durante-após a corrida |

---

### drivers

Informações dos pilotos de uma sessão.

```
/drivers?driver_number=1&session_key=9158
```

| Atributo | Descrição |
|---|---|
| `driver_number` | Número do piloto |
| `broadcast_name` | Nome exibido na TV |
| `first_name`, `last_name`, `full_name` | Nomes |
| `name_acronym` | Sigla de 3 letras |
| `headshot_url` | URL da foto |
| `team_name` | Equipe |
| `team_colour` | Cor da equipe (hex RRGGBB) |
| `country_code` | **Deprecado** — será removido no fim da temporada 2026 |
| `meeting_key`, `session_key` | Chaves |

---

### intervals

Intervalo entre pilotos e distância para o líder. Apenas corridas, atualização ~4 s.

```
/intervals?session_key=9165&interval>0&interval<0.005
```

| Atributo | Descrição |
|---|---|
| `date` | Data/hora UTC |
| `driver_number` | Número do piloto |
| `gap_to_leader` | Diferença para o líder (s), `+1 LAP` se retardatário, `null` para o líder |
| `interval` | Diferença para o carro à frente (s), `+1 LAP` se retardatário, `null` para o líder |
| `meeting_key`, `session_key` | Chaves |

---

### laps

Dados detalhados de cada volta.

```
/laps?session_key=9161&driver_number=63&lap_number=8
```

| Atributo | Descrição |
|---|---|
| `lap_number` | Número da volta (começa em 1) |
| `lap_duration` | Tempo total da volta (s) |
| `duration_sector_1/2/3` | Tempo de cada setor (s) |
| `date_start` | Início da volta (aproximado) |
| `i1_speed`, `i2_speed` | Velocidade nos pontos intermediários (km/h) |
| `st_speed` | Velocidade no speed trap (km/h) |
| `is_pit_out_lap` | Se é volta de saída dos boxes |
| `segments_sector_1/2/3` | Lista de mini-setores (tabela abaixo) |
| `driver_number`, `meeting_key`, `session_key` | Identificadores |

**Valores de segmento:**

| Valor | Significado |
|---|---|
| 0 | Não disponível |
| 2048 | Setor amarelo |
| 2049 | Setor verde |
| 2051 | Setor roxo |
| 2064 | Pit lane |
| 2050, 2052, 2068 | Desconhecido |

> Segmentos **não estão disponíveis em corridas** e podem divergir das cores mostradas na TV.

---

### location

Posição aproximada dos carros na pista, ~3,7 Hz. Serve para medir progresso na pista, mas não indica posição lateral. A origem `(0, 0, 0)` é arbitrária.

```
/location?session_key=9161&driver_number=81&date>2023-09-16T13:03:35.200&date<2023-09-16T13:03:35.800
```

| Atributo | Descrição |
|---|---|
| `date` | Data/hora UTC |
| `x`, `y`, `z` | Coordenadas cartesianas 3D aproximadas |
| `driver_number`, `meeting_key`, `session_key` | Identificadores |

---

### meetings

Informações sobre GPs e fins de semana de testes. Atualizado diariamente à meia-noite UTC.

```
/meetings?year=2026&country_name=Singapore
```

| Atributo | Descrição |
|---|---|
| `meeting_key` | Chave do meeting |
| `meeting_name`, `meeting_official_name` | Nome e nome oficial |
| `year` | Ano |
| `date_start`, `date_end` | Início e fim (UTC) |
| `gmt_offset` | Diferença para GMT no local |
| `is_cancelled` | Se foi cancelado |
| `location` | Cidade/local |
| `country_key`, `country_code`, `country_name`, `country_flag` | Dados do país |
| `circuit_key`, `circuit_short_name`, `circuit_type`, `circuit_image` | Dados do circuito (`Permanent`, `Temporary - Street` ou `Temporary - Road`) |
| `circuit_info_url` | JSON com informações detalhadas do circuito (dados do MultiViewer, formato FastF1) |

---

### overtakes

Ultrapassagens (inclui trocas de posição por pit stops ou punições pós-corrida). Apenas corridas; pode estar incompleto.

```
/overtakes?session_key=9636&overtaking_driver_number=63&overtaken_driver_number=4&position=1
```

| Atributo | Descrição |
|---|---|
| `date` | Data/hora UTC |
| `overtaking_driver_number` | Piloto que ultrapassou |
| `overtaken_driver_number` | Piloto ultrapassado |
| `position` | Posição do ultrapassador após a manobra |
| `meeting_key`, `session_key` | Chaves |

---

### pit

Passagens pelo pit lane.

```
/pit?session_key=9877&stop_duration<2.3
```

| Atributo | Descrição |
|---|---|
| `date` | Data/hora UTC |
| `driver_number` | Número do piloto |
| `lap_number` | Volta da parada |
| `lane_duration` | Tempo no pit lane (s) |
| `stop_duration` | Tempo parado (s) — disponível a partir do GP dos EUA de 2024 |
| `pit_duration` | **Deprecado** (igual a `lane_duration`) — será removido no fim da temporada 2026 |
| `meeting_key`, `session_key` | Chaves |

---

### position

Posição dos pilotos ao longo da sessão, incluindo a inicial e as mudanças.

```
/position?meeting_key=1217&driver_number=40&position<=3
```

| Atributo | Descrição |
|---|---|
| `date` | Data/hora UTC |
| `driver_number` | Número do piloto |
| `position` | Posição (começa em 1) |
| `meeting_key`, `session_key` | Chaves |

---

### race_control

Eventos da direção de prova: status da sessão, incidentes, bandeiras, safety car etc.

```
/race_control?flag=BLACK AND WHITE&driver_number=1&date>=2023-01-01&date<2023-09-01
```

| Atributo | Descrição |
|---|---|
| `category` | Categoria (`SessionStatus`, `CarEvent`, `Drs`, `Flag`, `SafetyCar`...) |
| `flag` | Bandeira (`GREEN`, `YELLOW`, `DOUBLE YELLOW`, `CHEQUERED`...) |
| `scope` | Escopo (`Track`, `Driver`, `Sector`...) |
| `message` | Descrição do evento |
| `date` | Data/hora UTC |
| `driver_number` | Piloto envolvido (se houver) |
| `lap_number` | Volta (em corrida) |
| `sector` | Mini-setor onde ocorreu |
| `qualifying_phase` | Fase (`1`, `2` ou `3`) em classificações |
| `meeting_key`, `session_key` | Chaves |

---

### sessions

Sessões de um GP ou teste (treinos, classificação, sprint, corrida). Atualizado diariamente à meia-noite UTC.

```
/sessions?country_name=Belgium&session_name=Sprint%20Qualifying&year=2023
```

| Atributo | Descrição |
|---|---|
| `session_key` | Chave da sessão |
| `session_name` | Nome (`Practice 1`, `Qualifying`, `Race`...) |
| `session_type` | Tipo (`Practice`, `Qualifying`, `Race`...) |
| `date_start`, `date_end` | Início e fim (UTC) |
| `gmt_offset` | Diferença para GMT |
| `is_cancelled` | Se foi cancelada |
| `location`, `country_*`, `circuit_*` | Local, país e circuito |
| `meeting_key` | Chave do meeting |
| `year` | Ano |

---

### session_result

Resultado final da sessão. Disponível poucos minutos após a publicação oficial no site da F1.

```
/session_result?session_key=7782&position<=3
```

| Atributo | Descrição |
|---|---|
| `position` | Posição final |
| `driver_number` | Número do piloto |
| `duration` | Melhor volta (treino/quali) ou tempo total (corrida), em segundos. Em quali é um array [Q1, Q2, Q3] |
| `gap_to_leader` | Diferença para o líder (s) ou `+N LAP(S)`. Em quali é um array [Q1, Q2, Q3] |
| `number_of_laps` | Voltas completadas |
| `dnf` | Não terminou (só quali e corrida) |
| `dns` | Não largou (só quali e corrida) |
| `dsq` | Desclassificado |
| `meeting_key`, `session_key` | Chaves |

---

### starting_grid

Grid de largada da próxima corrida. Disponível poucos minutos após o resultado oficial.

```
/starting_grid?session_key=7783&position<=3
```

| Atributo | Descrição |
|---|---|
| `position` | Posição no grid |
| `driver_number` | Número do piloto |
| `lap_duration` | Tempo da volta de classificação (s) |
| `meeting_key`, `session_key` | Chaves |

---

### stints

Períodos contínuos de pilotagem (stints), com informações de pneus.

```
/stints?session_key=9165&tyre_age_at_start>=3
```

| Atributo | Descrição |
|---|---|
| `stint_number` | Número do stint (começa em 1) |
| `lap_start`, `lap_end` | Primeira e última volta do stint |
| `compound` | Composto do pneu (`SOFT`, `MEDIUM`, `HARD`...) |
| `tyre_age_at_start` | Idade do pneu no início (voltas) |
| `driver_number`, `meeting_key`, `session_key` | Identificadores |

---

### team_radio

Rádios entre pilotos e equipes. Apenas uma seleção das comunicações é incluída.

> **Aviso:** a F1 não libera rádios para todas as sessões. A cobertura caiu bastante a partir de 2026, e a maioria dos eventos não tem dados de rádio. Isso é uma limitação da F1.

```
/team_radio?session_key=9158&driver_number=11
```

| Atributo | Descrição |
|---|---|
| `date` | Data/hora UTC |
| `driver_number` | Número do piloto |
| `recording_url` | URL do áudio (mp3) |
| `meeting_key`, `session_key` | Chaves |

---

### weather

Clima na pista, atualizado a cada minuto.

```
/weather?meeting_key=1208&wind_direction>=130&track_temperature>=52
```

| Atributo | Descrição |
|---|---|
| `date` | Data/hora UTC |
| `air_temperature` | Temperatura do ar (°C) |
| `track_temperature` | Temperatura da pista (°C) |
| `humidity` | Umidade relativa (%) |
| `pressure` | Pressão atmosférica (mbar) |
| `rainfall` | Indica se há chuva |
| `wind_speed` | Velocidade do vento (m/s) |
| `wind_direction` | Direção do vento (0°–359°) |
| `meeting_key`, `session_key` | Chaves |

---

## 6. Exemplo prático: descobrir e consultar uma sessão

```python
import json
from urllib.request import urlopen

BASE = "https://api.openf1.org/v1"


def get(path):
    return json.loads(urlopen(f"{BASE}/{path}").read().decode("utf-8"))


# 1. Achar a sessão de corrida de um GP
sessions = get("sessions?year=2023&country_name=Singapore&session_name=Race")
session_key = sessions[0]["session_key"]

# 2. Resultado final
resultado = get(f"session_result?session_key={session_key}&position<=3")

# 3. Pilotos da sessão
pilotos = get(f"drivers?session_key={session_key}")

print(resultado)
print([p["name_acronym"] for p in pilotos])
```

---

## 7. Avisos importantes

- Campos **deprecados** que serão removidos no fim da temporada 2026: `country_code` (em `/drivers`) e `pit_duration` (em `/pit`).
- `/intervals` e `/overtakes` funcionam apenas em corridas; `/championship_*` apenas em sessões de corrida.
- `segments_sector_*` não existem em corridas.
- Cobertura de `/team_radio` reduzida a partir de 2026.
- Dados em tempo real requerem assinatura; histórico (2023+) é livre.

---

## 8. Suporte e contribuição

- Dúvidas gerais: [GitHub Discussions](https://github.com/br-g/openf1/discussions)
- Bugs: [GitHub Issues](https://github.com/br-g/openf1/issues)
- Contato direto: https://openf1.org/contact
- Contribuir: [CONTRIBUTING.md](https://github.com/br-g/openf1/blob/main/CONTRIBUTING.md)
