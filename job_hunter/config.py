from __future__ import annotations

import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # dotenv é opcional (útil só em dev local)
    pass


# Localizações elegíveis para home office (proxy de idioma EN/PT).
# Casa como substring, case-insensitive, contra o local da vaga.
# Regiões lusófonas (PT) + anglófonas/abertas (EN).
DEFAULT_LOCATIONS = ",".join(
    [
        "worldwide",
        "anywhere",
        "americas",
        "north america",
        "south america",
        "latam",
        "latin america",
        "brazil",
        "brasil",
        "portugal",
        "usa",
        "united states",
        "canada",
        "uk",
        "united kingdom",
        "ireland",
        "australia",
        "new zealand",
        "europe",
        "emea",
    ]
)


# Sinais de entry-level / estágio (EN + PT). Casa como substring no
# título + tags + job_type da vaga.
DEFAULT_LEVEL_KEYWORDS = ",".join(
    [
        "intern",
        "internship",
        "junior",
        "júnior",
        "jr",
        "entry level",
        "entry-level",
        "graduate",
        "trainee",
        "apprentice",
        "new grad",
        "early career",
        "estagio",
        "estágio",
        "estagiario",
        "estagiário",
        "jovem aprendiz",
        "aprendiz",
    ]
)

# Sinais que vetam a vaga mesmo com match positivo (evita "Senior ... Program").
DEFAULT_LEVEL_EXCLUDE = ",".join(["senior", "sênior", "principal", "staff engineer"])


def _split(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _env(name: str, default: str = "") -> str:
    """Lê uma env var tratando string vazia/espaços como ausente.

    No GitHub Actions, um `${{ vars.X }}` de uma Variable não definida vira uma
    string vazia (não "unset"), então `os.getenv(name, default)` devolveria ""
    em vez do default. Este helper cai para o default nesse caso.
    """
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value


def _bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass
class Config:
    telegram_bot_token: str
    telegram_chat_id: str
    search_terms: list[str]
    keywords: list[str]
    remote_locations: list[str]
    allow_unknown_location: bool
    entry_level_only: bool
    level_keywords: list[str]
    level_exclude: list[str]
    database_path: str
    max_notifications: int
    notify_on_first_run: bool
    request_timeout: int
    user_agent: str

    @classmethod
    def from_env(cls) -> "Config":
        search_terms = _split(_env("JOB_SEARCH_TERMS", "python"))
        keywords = _split(_env("JOB_KEYWORDS", "")) or search_terms
        remote_locations = _split(_env("REMOTE_LOCATIONS", DEFAULT_LOCATIONS))
        level_keywords = _split(_env("LEVEL_KEYWORDS", DEFAULT_LEVEL_KEYWORDS))
        level_exclude = _split(_env("LEVEL_EXCLUDE", DEFAULT_LEVEL_EXCLUDE))
        return cls(
            telegram_bot_token=_env("TELEGRAM_BOT_TOKEN"),
            telegram_chat_id=_env("TELEGRAM_CHAT_ID"),
            search_terms=search_terms,
            keywords=[k.lower() for k in keywords],
            remote_locations=[loc.lower() for loc in remote_locations],
            allow_unknown_location=_bool(_env("ALLOW_UNKNOWN_LOCATION", "true")),
            entry_level_only=_bool(_env("ENTRY_LEVEL_ONLY", "true")),
            level_keywords=[k.lower() for k in level_keywords],
            level_exclude=[k.lower() for k in level_exclude],
            database_path=_env("DATABASE_PATH", "data/jobs.db"),
            max_notifications=int(_env("MAX_NOTIFICATIONS_PER_RUN", "20")),
            notify_on_first_run=_bool(_env("NOTIFY_ON_FIRST_RUN", "false")),
            request_timeout=int(_env("REQUEST_TIMEOUT", "30")),
            user_agent=_env(
                "USER_AGENT",
                "job-hunter/1.0 (+https://github.com/tommyogino/job-hunter)",
            ),
        )

    def validate(self) -> None:
        missing = []
        if not self.telegram_bot_token:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not self.telegram_chat_id:
            missing.append("TELEGRAM_CHAT_ID")
        if missing:
            raise SystemExit(
                "Configuração obrigatória ausente: " + ", ".join(missing)
            )
