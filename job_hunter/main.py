from __future__ import annotations

import logging
import time

import requests

from .config import Config
from .db import Database
from .models import Job
from .notify import TelegramNotifier, format_message
from .sources import remoteok, remotive

logger = logging.getLogger(__name__)


def collect_jobs(config: Config, session: requests.Session) -> list[Job]:
    """Coleta das duas fontes e deduplica por uid.

    Todas as vagas são home office (as duas APIs são remote-only). Aplica-se um
    filtro de localização elegível às duas fontes, como proxy de idioma (EN/PT).
    A Remotive já filtra por termo no servidor; na RemoteOK, que devolve a lista
    inteira, também se aplica o filtro de keywords localmente.
    """
    unique: dict[str, Job] = {}

    def eligible(job: Job) -> bool:
        if not job.location_allowed(
            config.remote_locations, config.allow_unknown_location
        ):
            return False
        if config.entry_level_only and not job.is_entry_level(
            config.level_keywords, config.level_exclude
        ):
            return False
        return True

    for job in remotive.fetch(config.search_terms, session, config.request_timeout):
        if eligible(job):
            unique[job.uid] = job

    for job in remoteok.fetch(session, config.request_timeout):
        if job.matches(config.keywords) and eligible(job):
            unique[job.uid] = job

    return list(unique.values())


def run(config: Config | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    config = config or Config.from_env()
    config.validate()

    session = requests.Session()
    session.headers.update(
        {"User-Agent": config.user_agent, "Accept": "application/json"}
    )

    db = Database(config.database_path)
    first_run = db.is_empty()

    jobs = collect_jobs(config, session)
    logger.info("Total de vagas que batem com o filtro: %d", len(jobs))

    new_jobs = db.filter_new(jobs)
    logger.info("Vagas novas (nunca vistas): %d", len(new_jobs))

    # Primeira execução: só semeia o banco para não inundar o Telegram.
    if first_run and not config.notify_on_first_run:
        logger.info("Primeira execução: semeando o banco sem notificar.")
        db.mark_all_seen(new_jobs)
        db.close()
        return 0

    if not new_jobs:
        db.close()
        return 0

    notifier = TelegramNotifier(
        config.telegram_bot_token,
        config.telegram_chat_id,
        session,
        config.request_timeout,
    )

    sent = 0
    # Vagas acima do cap ficam para a próxima execução (não são perdidas).
    for job in new_jobs[: config.max_notifications]:
        if notifier.send(format_message(job)):
            db.mark_seen(job)
            sent += 1
            time.sleep(0.5)  # gentileza com o rate limit do Telegram
        else:
            # Falha provavelmente global (token/rede). Não marca como visto,
            # para tentar de novo na próxima execução, e para a rodada.
            logger.warning("Interrompendo envios após falha.")
            break

    db.close()
    logger.info("Notificações enviadas: %d", sent)
    return sent
