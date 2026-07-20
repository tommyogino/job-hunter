from __future__ import annotations

import logging

import requests

from ..models import Job

logger = logging.getLogger(__name__)

API_URL = "https://remoteok.com/api"


def fetch(session: requests.Session, timeout: int) -> list[Job]:
    """Busca todas as vagas da RemoteOK (a API não tem busca server-side).

    A filtragem por palavra-chave acontece depois, em main.collect_jobs.
    O primeiro elemento do array é um aviso legal (sem 'id') e é ignorado.
    """
    jobs: list[Job] = []
    try:
        resp = session.get(API_URL, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as exc:
        logger.warning("RemoteOK falhou: %s", exc)
        return jobs

    if not isinstance(data, list):
        logger.warning("RemoteOK retornou formato inesperado")
        return jobs

    for item in data:
        if not isinstance(item, dict) or "id" not in item:
            continue  # pula o elemento de metadados/aviso legal
        ext_id = str(item.get("id", "")).strip()
        if not ext_id:
            continue
        jobs.append(
            Job(
                source="remoteok",
                external_id=ext_id,
                title=(item.get("position") or "").strip(),
                company=(item.get("company") or "").strip(),
                url=(item.get("url") or "").strip(),
                location=(item.get("location") or "").strip(),
                tags=tuple(item.get("tags") or ()),
            )
        )

    logger.info("RemoteOK: %d vagas coletadas", len(jobs))
    return jobs
