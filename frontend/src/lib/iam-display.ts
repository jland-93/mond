/**
 * IAM Identity/Permission 표시용 헬퍼.
 *
 * 외부 시스템에서 import한 식별자는 UUID(`00000000-0000-0000-0000-000000000001`),
 * ARN(`arn:aws:iam::123456789012:role/admin`), DN(`uid=alice,ou=people,...`) 같이
 * 사람이 한눈에 알아보기 어렵습니다. 화면에는 의미 있는 짧은 이름을 강조하고
 * 원본 식별자는 tooltip/보조 라인으로 보존합니다.
 */

import type { IAMIdentity, IdentityType, PermissionRow } from "@/lib/iam-api";

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const ARN_RE = /^arn:(aws|aws-cn|aws-us-gov):/;
const DN_RE = /^(cn|uid|ou|dc)=/i;

export interface DisplayLine {
  /** 큰 글씨로 보일 사람이 읽는 이름. */
  primary: string;
  /** 작은 글씨로 보일 부가 정보 (원본 ID · 출처 등). 없으면 undefined. */
  secondary?: string;
  /** tooltip에 보일 원본 전체 식별자. */
  tooltip?: string;
}

/** ARN에서 마지막 `/` 또는 `:` 이후 토큰을 추출. */
function tailOf(value: string): string {
  const slash = value.lastIndexOf("/");
  if (slash >= 0 && slash < value.length - 1) return value.slice(slash + 1);
  const colon = value.lastIndexOf(":");
  if (colon >= 0 && colon < value.length - 1) return value.slice(colon + 1);
  return value;
}

/** UUID는 짧게(`…7e3a`) — 사람이 비교만 할 수 있게. */
function shortUuid(uuid: string): string {
  return `…${uuid.slice(-6)}`;
}

/** DN에서 RDN(`uid=alice`)을 뽑고 그 값(alice)만 반환. */
function tailOfDn(dn: string): string {
  const first = dn.split(",")[0] ?? dn;
  const eq = first.indexOf("=");
  return eq >= 0 ? first.slice(eq + 1).trim() : first.trim();
}

export function identityDisplay(i: IAMIdentity): DisplayLine {
  // 사용자가 attributes.display_name 또는 attributes.email을 채워뒀다면 우선 사용
  const attrs = (i.attributes ?? {}) as Record<string, unknown>;
  const displayName =
    (typeof attrs.display_name === "string" && attrs.display_name) ||
    (typeof attrs.displayName === "string" && attrs.displayName) ||
    (typeof attrs.email === "string" && attrs.email) ||
    (typeof attrs.mail === "string" && attrs.mail) ||
    null;

  const raw = (i.external_id || i.name || "").trim();

  if (displayName) {
    return { primary: displayName, secondary: raw || undefined, tooltip: raw || undefined };
  }

  // ARN
  if (ARN_RE.test(raw)) {
    const tail = tailOf(raw);
    return { primary: tail || raw, secondary: raw, tooltip: raw };
  }

  // GCP member 표기(`user:alice@corp.com` 등) — prefix는 type tag로 흡수, 뒷부분만
  const colon = raw.indexOf(":");
  if (colon > 0 && colon < 20 && raw.length > colon + 1 && !raw.startsWith("arn:")) {
    const head = raw.slice(0, colon).toLowerCase();
    const tail = raw.slice(colon + 1);
    if (["user", "group", "serviceaccount", "domain"].includes(head)) {
      return { primary: tail, secondary: raw, tooltip: raw };
    }
  }

  // LDAP DN
  if (DN_RE.test(raw)) {
    return { primary: tailOfDn(raw), secondary: raw, tooltip: raw };
  }

  // UUID — Azure AD object id / Identity Center principalId 등
  if (UUID_RE.test(raw)) {
    return {
      primary: i.name && i.name !== raw ? i.name : shortUuid(raw),
      secondary: raw,
      tooltip: raw,
    };
  }

  // 그 외 — 이름을 그대로
  return {
    primary: i.name || raw || "(unnamed)",
    secondary: raw !== i.name ? raw : undefined,
    tooltip: raw || undefined,
  };
}

export function permissionDisplay(p: PermissionRow): DisplayLine {
  const raw = (p.external_id || p.name || "").trim();

  // ARN
  if (ARN_RE.test(raw)) {
    return { primary: tailOf(raw), secondary: raw, tooltip: raw };
  }

  // GCP roles/owner 처럼 짧은 식별자는 그대로
  if (raw.startsWith("roles/")) {
    return { primary: raw, tooltip: raw };
  }

  // Azure roleDefinition path
  if (raw.includes("/providers/Microsoft.Authorization/roleDefinitions/")) {
    return { primary: p.name || tailOf(raw), secondary: raw, tooltip: raw };
  }

  return {
    primary: p.name || raw || "(unnamed)",
    secondary: raw !== p.name ? raw : undefined,
    tooltip: raw || undefined,
  };
}

export const IDENTITY_TYPE_COLOR: Record<IdentityType, string> = {
  user: "blue",
  role: "geekblue",
  service_account: "purple",
  group: "cyan",
  sso_user: "magenta",
  sso_group: "magenta",
};

/** 검색 텍스트가 identity의 어느 필드에든 포함되는지 (대소문자 무시). */
export function identityMatches(i: IAMIdentity, q: string): boolean {
  if (!q) return true;
  const needle = q.toLowerCase();
  return [i.name, i.external_id, JSON.stringify(i.attributes ?? {})]
    .filter(Boolean)
    .some((s) => (s as string).toLowerCase().includes(needle));
}

export function permissionMatches(p: PermissionRow, q: string): boolean {
  if (!q) return true;
  const needle = q.toLowerCase();
  return [p.name, p.external_id, p.description, p.risk_hint]
    .filter(Boolean)
    .some((s) => (s as string).toLowerCase().includes(needle));
}
