from __future__ import annotations

import logging

import requests

from ..models import Job

logger = logging.getLogger(__name__)

API_URL = "https://remotive.com/api/remote-jobs"


def fetch(search_terms: list[str], session: requests.Session, timeout: int) -> list[Job]:
    """Busca vagas na Remotive, um request por termo de busca."""
    jobs: list[Job] = []
    seen_ids: set[str] = set()
    terms = search_terms or [""]

    for term in terms:
        params: dict[str, object] = {"limit": 50}
        if term:
            params["search"] = term
        try:
            resp = session.get(API_URL, params=params, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, ValueError) as exc:
            logger.warning("Remotive falhou para %r: %s", term, exc)
            continue

        for item in data.get("jobs", []):
            ext_id = str(item.get("id", "")).strip()
            if not ext_id or ext_id in seen_ids:
                continue
            seen_ids.add(ext_id)
            jobs.append(
                Job(
                    source="remotive",
                    external_id=ext_id,
                    title=(item.get("title") or "").strip(),
                    company=(item.get("company_name") or "").strip(),
                    url=(item.get("url") or "").strip(),
                    location=(item.get("candidate_required_location") or "").strip(),
                    tags=tuple(item.get("tags") or ()),
                    job_type=(item.get("job_type") or "").strip(),
                )
            )

    logger.info("Remotive: %d vagas coletadas", len(jobs))
    return jobs
