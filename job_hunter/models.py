from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Job:
    """Uma vaga normalizada, independente da fonte."""

    source: str
    external_id: str
    title: str
    company: str
    url: str
    location: str = ""
    tags: tuple[str, ...] = ()
    job_type: str = ""

    @property
    def uid(self) -> str:
        """Identificador estável e único entre as fontes."""
        return f"{self.source}:{self.external_id}"

    def matches(self, keywords: list[str]) -> bool:
        """True se algum keyword (lowercase) aparecer no título/empresa/local/tags."""
        if not keywords:
            return True
        haystack = " ".join(
            [self.title, self.company, self.location, " ".join(self.tags)]
        ).lower()
        return any(kw in haystack for kw in keywords)

    def location_allowed(
        self, allowed: list[str], allow_unknown: bool = True
    ) -> bool:
        """True se o local da vaga casar com alguma localização elegível.

        Usado como proxy de idioma (EN/PT) para vagas home office. Quando o local
        vem vazio (comum na RemoteOK), respeita `allow_unknown`.
        """
        loc = self.location.strip().lower()
        if not loc:
            return allow_unknown
        if not allowed:
            return True
        return any(a in loc for a in allowed)

    def is_entry_level(self, include: list[str], exclude: list[str]) -> bool:
        """True se a vaga tiver sinal de entry-level/estágio.

        Nenhuma das APIs tem campo de senioridade, então usa-se palavra-chave no
        título + tags + job_type. Sem `include`, não filtra. Um match em `exclude`
        (ex: 'senior') veta a vaga mesmo que tenha algum sinal positivo.
        """
        if not include:
            return True
        haystack = " ".join([self.title, self.job_type, " ".join(self.tags)]).lower()
        if not any(kw in haystack for kw in include):
            return False
        if exclude and any(kw in haystack for kw in exclude):
            return False
        return True
