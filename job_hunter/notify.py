from __future__ import annotations

import html
import logging
import time

import requests

from .models import Job

logger = logging.getLogger(__name__)

API_TEMPLATE = "https://api.telegram.org/bot{token}/sendMessage"


def format_message(job: Job) -> str:
    parts = [f"<b>{html.escape(job.title or 'Vaga sem título')}</b>"]
    if job.company:
        parts.append(f"🏢 {html.escape(job.company)}")
    if job.location:
        parts.append(f"📍 {html.escape(job.location)}")
    if job.url:
        parts.append(f"🔗 {html.escape(job.url)}")
    parts.append(f"<i>via {html.escape(job.source)}</i>")
    return "\n".join(parts)


class TelegramNotifier:
    def __init__(
        self,
        token: str,
        chat_id: str,
        session: requests.Session,
        timeout: int = 30,
    ):
        self.url = API_TEMPLATE.format(token=token)
        self.chat_id = chat_id
        self.session = session
        self.timeout = timeout

    def send(self, text: str) -> bool:
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }
        try:
            resp = self.session.post(self.url, json=payload, timeout=self.timeout)
            if resp.status_code == 429:
                retry_after = 1
                try:
                    retry_after = resp.json().get("parameters", {}).get("retry_after", 1)
                except ValueError:
                    pass
                logger.info("Rate limit do Telegram; aguardando %ss", retry_after)
                time.sleep(retry_after + 1)
                resp = self.session.post(self.url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            return True
        except requests.RequestException as exc:
            logger.warning("Envio ao Telegram falhou: %s", exc)
            return False
