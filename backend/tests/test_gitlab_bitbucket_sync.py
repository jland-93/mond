"""
GitLab / Bitbucket sync — 외부 호출 없는 라벨/상태 도출 invariant.

discover_* 함수는 GitHub sync와 같은 패턴을 따르고 외부 의존이라 통합 환경에서만
의미 있는 검증이 된다. 여기선 순수 함수 + status_payload 분기만 검증.
"""

from app.core.config import settings
from app.services import bitbucket_sync, gitlab_sync


# ── GitLab ──────────────────────────────────────────────
def test_gitlab_labels_visibility_private():
    labels = gitlab_sync._labels_from_project(
        {"default_branch": "develop", "archived": False, "visibility": "private"}
    )
    assert labels["source"] == "gitlab_sync"
    assert labels["default_branch"] == "develop"
    assert labels["archived"] is False
    assert labels["visibility"] == "private"


def test_gitlab_labels_default_branch_falls_back_to_main():
    labels = gitlab_sync._labels_from_project({"visibility": "internal"})
    assert labels["default_branch"] == "main"
    assert labels["visibility"] == "internal"


def test_gitlab_status_uses_api_url_default(monkeypatch):
    monkeypatch.setattr(settings, "GITLAB_TOKEN", None)
    monkeypatch.setattr(settings, "GITLAB_GROUP", None)
    monkeypatch.setattr(settings, "GITLAB_API_URL", None)
    s = gitlab_sync.status_payload()
    assert s["token_configured"] is False
    assert s["default_group"] is None
    assert s["api_url"] == "https://gitlab.com/api/v4"


def test_gitlab_status_self_hosted_url(monkeypatch):
    monkeypatch.setattr(settings, "GITLAB_API_URL", "https://gitlab.example.internal/api/v4")
    monkeypatch.setattr(settings, "GITLAB_TOKEN", "glpat-x")
    monkeypatch.setattr(settings, "GITLAB_GROUP", "platform")
    s = gitlab_sync.status_payload()
    assert s["api_url"].startswith("https://gitlab.example.internal")
    assert s["token_configured"] is True
    assert s["default_group"] == "platform"


# ── Bitbucket ──────────────────────────────────────────
def test_bitbucket_labels_main_branch_from_nested():
    labels = bitbucket_sync._labels_from_repo(
        {"language": "Python", "is_private": True, "mainbranch": {"name": "develop"}}
    )
    assert labels["source"] == "bitbucket_sync"
    assert labels["language"] == "Python"
    assert labels["is_private"] is True
    assert labels["main_branch"] == "develop"


def test_bitbucket_labels_main_branch_falls_back():
    labels = bitbucket_sync._labels_from_repo({"language": None, "is_private": False})
    assert labels["main_branch"] == "main"
    assert labels["language"] == "unknown"
    assert labels["is_private"] is False


def test_bitbucket_status_credentials_complete(monkeypatch):
    monkeypatch.setattr(settings, "BITBUCKET_USERNAME", "alice")
    monkeypatch.setattr(settings, "BITBUCKET_APP_PASSWORD", "secret")
    monkeypatch.setattr(settings, "BITBUCKET_WORKSPACE", "my-team")
    s = bitbucket_sync.status_payload()
    assert s["credentials_configured"] is True
    assert s["default_workspace"] == "my-team"


def test_bitbucket_status_credentials_partial(monkeypatch):
    monkeypatch.setattr(settings, "BITBUCKET_USERNAME", "alice")
    monkeypatch.setattr(settings, "BITBUCKET_APP_PASSWORD", None)
    s = bitbucket_sync.status_payload()
    assert s["credentials_configured"] is False
