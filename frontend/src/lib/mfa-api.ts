/**
 * MFA API helpers — 패스키 + TOTP + 백업 코드
 *
 * @simplewebauthn/browser의 startRegistration/startAuthentication에 그대로 넘기는
 * options 객체와, complete 단계에 보낼 credential 객체를 다룬다.
 */

import { api } from "@/lib/api";

export interface MfaStatus {
  required: boolean;
  enrolled: boolean;
  passkeys: {
    id: number;
    name: string;
    transports: string[];
    created_at?: string | null;
    last_used_at?: string | null;
  }[];
  totp_confirmed: boolean;
  backup_codes_remaining: number;
}

export const mfaApi = {
  status: () => api.get<MfaStatus>("/auth/mfa/status").then((r) => r.data),

  // ── Passkey ─────────────────────────────────────────────
  passkeyRegisterBegin: () =>
    api.post<Record<string, unknown>>("/auth/mfa/passkey/register/begin").then((r) => r.data),
  passkeyRegisterComplete: (name: string, credential: Record<string, unknown>) =>
    api
      .post<{ id: number; name: string }>("/auth/mfa/passkey/register/complete", { name, credential })
      .then((r) => r.data),
  passkeyDelete: (credId: number) =>
    api.delete(`/auth/mfa/passkey/${credId}`).then((r) => r.data),

  passkeyLoginBegin: () =>
    api.post<Record<string, unknown>>("/auth/mfa/passkey/login/begin").then((r) => r.data),
  passkeyLoginComplete: (credential: Record<string, unknown>) =>
    api.post<{ ok: boolean }>("/auth/mfa/passkey/login/complete", { credential }).then((r) => r.data),

  // ── TOTP ────────────────────────────────────────────────
  totpSetup: () =>
    api
      .post<{ secret: string; uri: string; qr_png_base64: string }>("/auth/mfa/totp/setup")
      .then((r) => r.data),
  totpVerify: (code: string) =>
    api.post<{ ok: boolean }>("/auth/mfa/totp/verify", { code }).then((r) => r.data),
  totpChallenge: (code: string) =>
    api.post<{ ok: boolean }>("/auth/mfa/totp/challenge", { code }).then((r) => r.data),
  totpDisable: () => api.delete("/auth/mfa/totp").then((r) => r.data),

  // ── Backup codes ────────────────────────────────────────
  backupCodesRegenerate: () =>
    api.post<{ codes: string[] }>("/auth/mfa/backup-codes/regenerate").then((r) => r.data),
  backupCodeChallenge: (code: string) =>
    api
      .post<{ ok: boolean }>("/auth/mfa/backup-codes/challenge", { code })
      .then((r) => r.data),
};
