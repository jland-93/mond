"""
GCP/Azure IAM attach/detach 멱등성 + 충돌 재시도 동작 테스트

SDK 의존을 피하기 위해 사용 함수만 직접 검증.
"""

from app.iam.providers import gcp
from app.models.iam import IAMIdentity, IdentityType


def test_normalize_member_user_without_prefix():
    ident = IAMIdentity(identity_type=IdentityType.USER, name="alice", external_id="alice@corp.com")
    assert gcp._normalize_member(ident) == "user:alice@corp.com"


def test_normalize_member_group_prefix():
    ident = IAMIdentity(identity_type=IdentityType.GROUP, name="devops", external_id="devops@corp.com")
    assert gcp._normalize_member(ident) == "group:devops@corp.com"


def test_normalize_member_serviceaccount_prefix():
    ident = IAMIdentity(
        identity_type=IdentityType.SERVICE_ACCOUNT,
        name="ci",
        external_id="ci@demo.iam.gserviceaccount.com",
    )
    assert gcp._normalize_member(ident) == "serviceAccount:ci@demo.iam.gserviceaccount.com"


def test_normalize_member_preserves_existing_prefix():
    ident = IAMIdentity(
        identity_type=IdentityType.USER, name="x", external_id="user:already@corp.com"
    )
    assert gcp._normalize_member(ident) == "user:already@corp.com"


def test_normalize_member_empty():
    ident = IAMIdentity(identity_type=IdentityType.USER, name="", external_id=None)
    assert gcp._normalize_member(ident) == ""


def test_retryable_hints_contains_etag():
    # 에러 메시지 분기가 정상 동작하는 키워드 셋
    assert any(h in "Aborted: etag mismatch".lower() for h in gcp._RETRYABLE_HINTS)
    assert any(h in "concurrent modification".lower() for h in gcp._RETRYABLE_HINTS)
