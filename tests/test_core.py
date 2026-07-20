from job_hunter.config import Config
from job_hunter.db import Database
from job_hunter.models import Job
from job_hunter.notify import format_message


def make_job(**kw) -> Job:
    base = dict(
        source="remotive",
        external_id="1",
        title="Senior Python Engineer",
        company="Acme",
        url="https://example.com/1",
        location="Worldwide",
        tags=("python", "django"),
    )
    base.update(kw)
    return Job(**base)


def test_uid_is_source_and_id():
    assert make_job(source="remoteok", external_id="9").uid == "remoteok:9"


def test_matches_keyword_in_tags():
    job = make_job(title="Engineer", tags=("django",))
    assert job.matches(["django"])
    assert not job.matches(["golang"])


def test_matches_empty_keywords_is_true():
    assert make_job().matches([])


LOCS = ["worldwide", "brazil", "usa", "europe"]


def test_location_allowed_matches_substring():
    assert make_job(location="🌎 Worldwide").location_allowed(LOCS)
    assert make_job(location="Brazil").location_allowed(LOCS)
    assert not make_job(location="Germany only").location_allowed(LOCS)


def test_location_unknown_respects_flag():
    job = make_job(location="")
    assert job.location_allowed(LOCS, allow_unknown=True)
    assert not job.location_allowed(LOCS, allow_unknown=False)


def test_location_empty_allowlist_allows_all():
    assert make_job(location="Germany only").location_allowed([])


INCLUDE = ["intern", "internship", "junior", "estágio", "trainee"]
EXCLUDE = ["senior", "principal"]


def test_entry_level_matches_title_and_type():
    assert make_job(title="Junior Backend Developer").is_entry_level(INCLUDE, EXCLUDE)
    assert make_job(title="Software Engineer", job_type="internship").is_entry_level(
        INCLUDE, EXCLUDE
    )
    assert make_job(title="Vaga de Estágio em Dados").is_entry_level(INCLUDE, EXCLUDE)


def test_entry_level_rejects_senior_and_neutral():
    assert not make_job(title="Senior Python Engineer").is_entry_level(INCLUDE, EXCLUDE)
    assert not make_job(title="Backend Developer").is_entry_level(INCLUDE, EXCLUDE)


def test_entry_level_exclude_vetoes_positive_match():
    job = make_job(title="Senior Manager, Graduate Program")
    assert job.is_entry_level(["graduate"], ["senior"]) is False


def test_entry_level_empty_include_allows_all():
    assert make_job(title="Senior Python Engineer").is_entry_level([], EXCLUDE)


def test_db_filter_new_and_mark_seen():
    db = Database(":memory:")
    a, b = make_job(external_id="1"), make_job(external_id="2")

    assert db.is_empty()
    assert db.filter_new([a, b]) == [a, b]

    db.mark_seen(a)
    db.commit()

    assert not db.is_empty()
    assert db.filter_new([a, b]) == [b]
    db.close()


def test_empty_env_vars_fall_back_to_defaults(monkeypatch):
    # No GitHub Actions, vars não definidas viram string vazia, não "unset".
    for name in [
        "MAX_NOTIFICATIONS_PER_RUN",
        "REQUEST_TIMEOUT",
        "JOB_SEARCH_TERMS",
        "NOTIFY_ON_FIRST_RUN",
        "ENTRY_LEVEL_ONLY",
    ]:
        monkeypatch.setenv(name, "")
    cfg = Config.from_env()  # não pode levantar ValueError
    assert cfg.max_notifications == 20
    assert cfg.request_timeout == 30
    assert cfg.search_terms == ["python"]


def test_format_message_escapes_html():
    job = make_job(title="C++ & <script>", company="A&B")
    msg = format_message(job)
    assert "&lt;script&gt;" in msg
    assert "A&amp;B" in msg
