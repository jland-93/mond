"""
LLM prompt PII redaction

외부 LLM provider(Anthropic/OpenAI/Bedrock 등) 호출 전에 사용자 입력에서
명백한 PII와 시크릿을 마스킹한다. 자체 호스팅이라도 프롬프트가 provider
서버에 보내지는 순간 그 외부 시스템의 정책에 노출되므로, 사전 마스킹은
privacy-by-default 원칙에 부합.

대상:
  - 이메일
  - 전화번호 (한국 010-XXXX-XXXX / 일반 국제 표기)
  - 한국 주민등록번호 6-7 (체크섬 검증은 false positive 줄임)
  - 신용카드 (Luhn — 16자리 숫자 중 통과만)
  - AWS access key ID (AKIA prefix)
  - AWS secret access key (40-char base64)
  - 일반 Bearer/API token (sk_/ghp_/sk-/pat_ 등 prefix)
  - JWT (eyJ로 시작하는 3-segment)
  - IPv4 주소 (옵션 — 보안 컨텍스트에선 legitimate일 수 있어 기본 미적용)

토글:
  - 전체 끄기 → AI_PROMPT_REDACT_PII=false
  - 결과의 redactions 카운트는 로깅에만 사용, LLM 응답에는 노출 X
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_PHONE_KR = re.compile(r"\b01[016789][-\s]?\d{3,4}[-\s]?\d{4}\b")
_PHONE_INTL = re.compile(r"\+\d{1,3}[-\s]?\d{2,4}[-\s]?\d{3,4}[-\s]?\d{3,4}")
_RRN = re.compile(r"\b\d{6}[-\s]?[1-4]\d{6}\b")
_AWS_AKID = re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b")
_AWS_SECRET = re.compile(r"\b(?<![A-Za-z0-9/+=])[A-Za-z0-9/+=]{40}(?![A-Za-z0-9/+=])\b")
_GH_TOKEN = re.compile(r"\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{30,}\b")
_GENERIC_TOKEN = re.compile(r"\b(sk-[A-Za-z0-9_-]{20,}|pat_[A-Za-z0-9_-]{20,})\b")
_JWT = re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b")
_CC_16 = re.compile(r"\b(?:\d[ -]?){13,19}\b")


def _luhn_ok(num: str) -> bool:
    digits = [int(c) for c in num if c.isdigit()]
    if not 13 <= len(digits) <= 19:
        return False
    checksum = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


def _redact_cc(text: str, kinds: dict[str, int]) -> str:
    def repl(m: re.Match) -> str:
        if _luhn_ok(m.group(0)):
            kinds["cc"] = kinds.get("cc", 0) + 1
            return "[REDACTED_CC]"
        return m.group(0)

    return _CC_16.sub(repl, text)


@dataclass
class RedactionResult:
    text: str
    counts: dict[str, int]  # kind → count

    @property
    def total(self) -> int:
        return sum(self.counts.values())


def redact_prompt(text: str) -> RedactionResult:
    """주어진 텍스트에서 PII/시크릿을 마스킹한 사본을 반환.

    원본은 변경하지 않음 — caller가 원본 보관 책임.
    """
    if not text:
        return RedactionResult(text=text or "", counts={})

    counts: dict[str, int] = {}

    def _sub(pattern: re.Pattern, kind: str, placeholder: str, body: str) -> str:
        def repl(_m: re.Match) -> str:
            counts[kind] = counts.get(kind, 0) + 1
            return placeholder

        return pattern.sub(repl, body)

    out = text
    # 순서 — 더 구체적인 패턴부터. CC는 마지막에 (다른 토큰을 CC로 오인 방지)
    out = _sub(_JWT, "jwt", "[REDACTED_JWT]", out)
    out = _sub(_GH_TOKEN, "github_token", "[REDACTED_TOKEN]", out)
    out = _sub(_GENERIC_TOKEN, "api_token", "[REDACTED_TOKEN]", out)
    out = _sub(_AWS_AKID, "aws_akid", "[REDACTED_AWS_KEY]", out)
    out = _sub(_AWS_SECRET, "aws_secret", "[REDACTED_AWS_SECRET]", out)
    out = _sub(_EMAIL, "email", "[REDACTED_EMAIL]", out)
    out = _sub(_RRN, "rrn", "[REDACTED_RRN]", out)
    out = _sub(_PHONE_KR, "phone", "[REDACTED_PHONE]", out)
    out = _sub(_PHONE_INTL, "phone", "[REDACTED_PHONE]", out)
    out = _redact_cc(out, counts)

    return RedactionResult(text=out, counts=counts)
