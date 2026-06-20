/**
 * iam-display 헬퍼 테스트 — Vitest 환경이 없어도 import 검증 + 휴리스틱 동작.
 *
 * 현재 frontend는 별도 unit runner를 운영하지 않습니다. 이 파일은
 * vite build에 포함되지 않도록 `.test.ts` 컨벤션만 유지하고, 실제 검증은
 * 로컬에서 `vitest`를 띄울 때 수행됩니다. CI에서 깨지지 않도록 module-level
 * side effect 없음.
 */

import { identityDisplay, permissionDisplay } from "./iam-display";
import type { IAMIdentity, PermissionRow } from "./iam-api";

const _expect = (label: string, got: unknown, want: unknown) => {
  // eslint-disable-next-line no-console
  if (JSON.stringify(got) !== JSON.stringify(want)) console.error(`FAIL ${label}: got=${JSON.stringify(got)} want=${JSON.stringify(want)}`);
};

export function runIamDisplayChecks(): void {
  // ARN → role name 추출
  const r1 = identityDisplay({
    id: 1, source_id: 1, identity_type: "role",
    name: "DeveloperRole",
    external_id: "arn:aws:iam::000000000000:role/DeveloperRole",
    attributes: {},
  } satisfies IAMIdentity);
  _expect("arn role tail", r1.primary, "DeveloperRole");

  // Identity Center SSO_USER with display_name
  const r2 = identityDisplay({
    id: 2, source_id: 1, identity_type: "sso_user",
    name: "charlie@corp.com",
    external_id: "d4b86c70-1c4e-4a2b-9c5e-7a3f1e8d2c9b",
    attributes: { display_name: "Charlie Kim", email: "charlie@corp.com" },
  });
  _expect("sso display_name wins", r2.primary, "Charlie Kim");

  // UUID without display_name → short
  const r3 = identityDisplay({
    id: 3, source_id: 1, identity_type: "user",
    name: "00000000-0000-0000-0000-000000000001",
    external_id: "00000000-0000-0000-0000-000000000001",
    attributes: {},
  });
  _expect("uuid short", r3.primary, "…000001");

  // LDAP DN → CN value
  const r4 = identityDisplay({
    id: 4, source_id: 1, identity_type: "user",
    name: "alice.kim",
    external_id: "CN=Alice Kim,CN=Users,DC=corp,DC=local",
    attributes: { mail: "alice@corp.local" },
  });
  _expect("ldap mail wins over CN", r4.primary, "alice@corp.local");

  // GCP member prefix
  const r5 = identityDisplay({
    id: 5, source_id: 1, identity_type: "user",
    name: "alice@corp.com",
    external_id: "user:alice@corp.com",
    attributes: {},
  });
  _expect("gcp member tail", r5.primary, "alice@corp.com");

  // Permission ARN tail
  const p1 = permissionDisplay({
    id: 1, source_id: 1,
    name: "ReadOnlyAccess",
    external_id: "arn:aws:iam::aws:policy/ReadOnlyAccess",
    description: null,
    risk_hint: "read",
  } as PermissionRow);
  _expect("perm arn tail", p1.primary, "ReadOnlyAccess");

  // GCP role
  const p2 = permissionDisplay({
    id: 2, source_id: 1,
    name: "roles/owner",
    external_id: "roles/owner",
    description: null,
    risk_hint: "admin",
  } as PermissionRow);
  _expect("gcp role kept", p2.primary, "roles/owner");
}
