from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from typing import Iterable

from .models import Job

SCHEMA = """
CREATE TABLE IF NOT EXISTS seen_jobs (
    uid           TEXT PRIMARY KEY,
    source        TEXT NOT NULL,
    external_id   TEXT NOT NULL,
    title         TEXT,
    company       TEXT,
    url           TEXT,
    first_seen_at TEXT NOT NULL
);
"""


class Database:
    """Registro do que já foi visto, em SQLite."""

    def __init__(self, path: str):
        self.path = path
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.execute(SCHEMA)
        self.conn.commit()

    def is_empty(self) -> bool:
        cur = self.conn.execute("SELECT COUNT(*) FROM seen_jobs")
        return cur.fetchone()[0] == 0

    def filter_new(self, jobs: Iterable[Job]) -> list[Job]:
        new: list[Job] = []
        for job in jobs:
            cur = self.conn.execute(
                "SELECT 1 FROM seen_jobs WHERE uid = ?", (job.uid,)
            )
            if cur.fetchone() is None:
                new.append(job)
        return new

    def mark_seen(self, job: Job) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO seen_jobs "
            "(uid, source, external_id, title, company, url, first_seen_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                job.uid,
                job.source,
                job.external_id,
                job.title,
                job.company,
                job.url,
                datetime.now(timezone.utc).isoformat(),
            ),
        )

    def mark_all_seen(self, jobs: Iterable[Job]) -> None:
        for job in jobs:
            self.mark_seen(job)
        self.conn.commit()

    def commit(self) -> None:
        self.conn.commit()

    def close(self) -> None:
        self.conn.commit()
        self.conn.close()
