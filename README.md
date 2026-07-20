# job-hunter

Busca vagas remotas nas APIs da **Remotive** e da **RemoteOK**, guarda o que já
viu num **SQLite** e notifica as vagas novas no **Telegram**. Roda sozinho via
**GitHub Actions**.

## Como funciona

1. Coleta vagas da Remotive (com busca por termos) e da RemoteOK (lista completa).
2. Filtra por palavras-chave, deduplica e compara com o banco `data/jobs.db`.
3. Envia as vagas inéditas para o Telegram e marca como vistas.
4. No GitHub Actions, o `data/jobs.db` é commitado de volta ao repositório —
   é assim que o estado persiste entre execuções (os runners são efêmeros).

> Na **primeira execução** o banco está vazio; para não inundar o Telegram, ele
> apenas *semeia* o banco sem notificar. Coloque `NOTIFY_ON_FIRST_RUN=true` se
> quiser receber tudo de cara.

> **Escopo:** Remotive e RemoteOK são boards **100% remotos**, então só há vagas
> home office. Vagas **presenciais** (ex: Joinville/SC) exigiriam outra fonte e
> não são cobertas aqui. As remotas são limitadas a idioma EN/PT via
> `REMOTE_LOCATIONS` (aproximação por localização elegível).

## Configuração

| Variável | Obrigatória | Padrão | Descrição |
|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | sim | — | Token do bot (via @BotFather). |
| `TELEGRAM_CHAT_ID` | sim | — | ID do chat/canal de destino. |
| `JOB_SEARCH_TERMS` | não | `python` | Termos de busca da Remotive (separados por vírgula). |
| `JOB_KEYWORDS` | não | = `JOB_SEARCH_TERMS` | Filtro local aplicado só à RemoteOK (a Remotive já filtra no servidor). Vazio = sem filtro. |
| `REMOTE_LOCATIONS` | não | worldwide, americas, brazil, usa, uk, europe… | Localizações elegíveis (substring) usadas como proxy de idioma EN/PT, aplicado às duas fontes. Vazio = sem filtro. |
| `ALLOW_UNKNOWN_LOCATION` | não | `true` | Manter vagas sem local informado (comum na RemoteOK). |
| `ENTRY_LEVEL_ONLY` | não | `true` | Manter só entry-level/estágio (via palavras-chave em título+tags+job_type). |
| `LEVEL_KEYWORDS` | não | intern, junior, estágio, trainee… | Sinais de nível júnior/estágio (EN+PT). Vazio = sem filtro de nível. |
| `LEVEL_EXCLUDE` | não | senior, principal… | Vetam a vaga mesmo com match positivo. |
| `DATABASE_PATH` | não | `data/jobs.db` | Caminho do SQLite. |
| `MAX_NOTIFICATIONS_PER_RUN` | não | `20` | Cap de mensagens por execução. |
| `NOTIFY_ON_FIRST_RUN` | não | `false` | Notificar tudo na primeira execução? |
| `REQUEST_TIMEOUT` | não | `30` | Timeout HTTP (s). |
| `USER_AGENT` | não | `job-hunter/1.0 …` | A RemoteOK bloqueia UA vazio/genérico. |

## Rodar localmente

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # preencha token, chat id e filtros
python -m job_hunter
```

### Descobrir o `TELEGRAM_CHAT_ID`

1. Crie o bot com o **@BotFather** e copie o token.
2. Mande qualquer mensagem para o seu bot.
3. Acesse `https://api.telegram.org/bot<TOKEN>/getUpdates` e pegue o
   `message.chat.id`.

## GitHub Actions

O workflow [`.github/workflows/job-hunter.yml`](.github/workflows/job-hunter.yml)
roda a cada 3 horas (e no botão *Run workflow*). Configure em
**Settings → Secrets and variables → Actions**:

- **Secrets:** `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- **Variables** (opcionais): `JOB_SEARCH_TERMS`, `JOB_KEYWORDS`,
  `MAX_NOTIFICATIONS_PER_RUN`, `NOTIFY_ON_FIRST_RUN`

O job tem `permissions: contents: write` para commitar o `data/jobs.db`
atualizado. O commit usa `[skip ci]` para não disparar o workflow em loop.

## Testes

```bash
pip install pytest
pytest
```

## Estrutura

```
job_hunter/
├── config.py        # variáveis de ambiente
├── models.py        # dataclass Job (uid, filtro por keyword)
├── db.py            # SQLite: vagas vistas
├── notify.py        # Telegram
├── main.py          # orquestra coleta → filtro → notificação
├── __main__.py      # python -m job_hunter
└── sources/
    ├── remotive.py
    └── remoteok.py
```
