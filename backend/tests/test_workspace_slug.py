"""
Workspace slug 검증 — 순수 함수 invariant.
"""

import pytest

from app.services.workspace import is_valid_slug


@pytest.mark.parametrize(
    "slug",
    [
        "a",
        "default",
        "platform",
        "mobile-team",
        "team-2025",
        "abc-def-ghi",
        "x" * 64,
    ],
)
def test_valid_slugs(slug):
    assert is_valid_slug(slug) is True


@pytest.mark.parametrize(
    "slug",
    [
        "",                  # empty
        "A",                 # uppercase
        "Bad-Slug",          # uppercase letter
        "-leading",          # leading hyphen
        "trailing-",         # trailing hyphen
        "two..dots",         # invalid char
        "spaces here",       # spaces
        "x" * 65,            # 65자 — 한계 초과
        "한글",                # 비-ASCII
    ],
)
def test_invalid_slugs(slug):
    assert is_valid_slug(slug) is False
