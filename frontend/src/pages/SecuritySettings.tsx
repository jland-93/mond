/**
 * 보안 설정 — 패스키 등록·삭제, TOTP setup/disable, 백업 코드
 */

import {
  ApiOutlined,
  CopyOutlined,
  DeleteOutlined,
  KeyOutlined,
  MobileOutlined,
  PlusOutlined,
  SafetyOutlined,
  TeamOutlined,
} from "@ant-design/icons";
import { startRegistration } from "@simplewebauthn/browser";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  Button,
  Card,
  Empty,
  Form,
  Input,
  List,
  Modal,
  Popconfirm,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from "antd";
import { useState } from "react";

import { useAuth } from "@/auth/AuthContext";
import { useI18n } from "@/i18n";
import { api, type Asset, type Page } from "@/lib/api";
import type { Role } from "@/lib/auth-api";
import { mfaApi } from "@/lib/mfa-api";
import { roleRequestsApi, type RoleRequestRow } from "@/lib/role-requests-api";
import {
  webhookTokensApi,
  type WebhookTokenCreated,
  type WebhookTokenRow,
} from "@/lib/webhook-tokens-api";

const { Title, Paragraph, Text } = Typography;

export default function SecuritySettings() {
  const { t, locale } = useI18n();
  const { refresh } = useAuth();
  const qc = useQueryClient();

  const { data: status, isLoading } = useQuery({
    queryKey: ["mfa-status"],
    queryFn: mfaApi.status,
  });

  const [passkeyName, setPasskeyName] = useState("");
  const [totpModal, setTotpModal] = useState<{
    open: boolean;
    qr?: string;
    secret?: string;
  }>({ open: false });
  const [totpCode, setTotpCode] = useState("");
  const [backupCodes, setBackupCodes] = useState<string[] | null>(null);

  const refreshAll = () => {
    qc.invalidateQueries({ queryKey: ["mfa-status"] });
    refresh();
  };

  // ── 패스키 등록 ───────────────────────────────
  const registerPasskey = useMutation({
    mutationFn: async () => {
      const name = passkeyName.trim() || (locale === "ko" ? "패스키" : "Passkey");
      const options = await mfaApi.passkeyRegisterBegin();
      const credential = await startRegistration({ optionsJSON: options as never });
      return mfaApi.passkeyRegisterComplete(name, credential as unknown as Record<string, unknown>);
    },
    onSuccess: (cred) => {
      message.success(`${cred.name} ${locale === "ko" ? "등록됨" : "registered"}`);
      setPasskeyName("");
      refreshAll();
    },
    onError: (e: Error & { response?: { data?: { detail?: string } } }) => {
      message.error(e.response?.data?.detail ?? e.message);
    },
  });

  const deletePasskey = useMutation({
    mutationFn: (id: number) => mfaApi.passkeyDelete(id),
    onSuccess: () => {
      message.success(locale === "ko" ? "삭제됨" : "Deleted");
      refreshAll();
    },
  });

  // ── TOTP ───────────────────────────────────────
  const setupTotp = useMutation({
    mutationFn: () => mfaApi.totpSetup(),
    onSuccess: (data) => {
      setTotpModal({ open: true, qr: data.qr_png_base64, secret: data.secret });
    },
  });

  const verifyTotp = useMutation({
    mutationFn: (code: string) => mfaApi.totpVerify(code),
    onSuccess: () => {
      message.success(locale === "ko" ? "TOTP 등록 완료" : "TOTP enrolled");
      setTotpModal({ open: false });
      setTotpCode("");
      refreshAll();
    },
    onError: (e: Error & { response?: { data?: { detail?: string } } }) => {
      message.error(e.response?.data?.detail ?? e.message);
    },
  });

  const disableTotp = useMutation({
    mutationFn: () => mfaApi.totpDisable(),
    onSuccess: () => {
      message.success(locale === "ko" ? "TOTP 비활성화" : "TOTP disabled");
      refreshAll();
    },
  });

  // ── Backup codes ───────────────────────────────
  const regenBackup = useMutation({
    mutationFn: () => mfaApi.backupCodesRegenerate(),
    onSuccess: (data) => {
      setBackupCodes(data.codes);
      refreshAll();
    },
  });

  return (
    <div>
      <Title level={2} style={{ marginBottom: 4 }}>
        {t.security.title}
      </Title>
      <Paragraph type="secondary">{t.security.desc}</Paragraph>

      {status?.required && !status.enrolled && (
        <Alert
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
          message={t.security.requiredWarning}
        />
      )}

      <Card
        title={
          <Space>
            <KeyOutlined />
            <span>{t.security.passkeys}</span>
          </Space>
        }
        style={{ marginBottom: 16 }}
        loading={isLoading}
      >
        <Paragraph type="secondary" style={{ marginBottom: 12 }}>
          {t.security.passkeysDesc}
        </Paragraph>
        <Space.Compact style={{ marginBottom: 12, width: "100%", maxWidth: 520 }}>
          <Input
            placeholder={t.security.passkeyNameHint}
            value={passkeyName}
            onChange={(e) => setPasskeyName(e.target.value)}
          />
          <Button
            type="primary"
            icon={<KeyOutlined />}
            loading={registerPasskey.isPending}
            onClick={() => registerPasskey.mutate()}
          >
            {t.security.addPasskey}
          </Button>
        </Space.Compact>

        {(status?.passkeys.length ?? 0) === 0 ? (
          <Empty description={t.security.noPasskeys} />
        ) : (
          <List
            dataSource={status?.passkeys ?? []}
            renderItem={(p) => (
              <List.Item
                actions={[
                  <Popconfirm
                    key="del"
                    title={t.security.confirmDeletePasskey}
                    okType="danger"
                    onConfirm={() => deletePasskey.mutate(p.id)}
                  >
                    <Button type="text" danger icon={<DeleteOutlined />} />
                  </Popconfirm>,
                ]}
              >
                <List.Item.Meta
                  title={
                    <Space>
                      <Text strong>{p.name}</Text>
                      {(p.transports ?? []).filter(Boolean).map((tr) => (
                        <Tag key={tr}>{tr}</Tag>
                      ))}
                    </Space>
                  }
                  description={
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {p.created_at?.slice(0, 19).replace("T", " ")}
                      {p.last_used_at &&
                        ` · ${t.security.lastUsed} ${p.last_used_at.slice(0, 19).replace("T", " ")}`}
                    </Text>
                  }
                />
              </List.Item>
            )}
          />
        )}
      </Card>

      <Card
        title={
          <Space>
            <MobileOutlined />
            <span>{t.security.totp}</span>
          </Space>
        }
        extra={
          status?.totp_confirmed ? (
            <Popconfirm
              title={t.security.confirmDisableTotp}
              okType="danger"
              onConfirm={() => disableTotp.mutate()}
            >
              <Button danger>{t.security.disableTotp}</Button>
            </Popconfirm>
          ) : (
            <Button type="primary" onClick={() => setupTotp.mutate()} loading={setupTotp.isPending}>
              {t.security.setupTotp}
            </Button>
          )
        }
        style={{ marginBottom: 16 }}
        loading={isLoading}
      >
        <Paragraph type="secondary">{t.security.totpDesc}</Paragraph>
        {status?.totp_confirmed && (
          <Tag color="green" icon={<SafetyOutlined />}>
            {t.security.enabled}
          </Tag>
        )}
      </Card>

      <Card
        title={
          <Space>
            <SafetyOutlined />
            <span>{t.security.backupCodes}</span>
          </Space>
        }
        extra={
          <Popconfirm
            title={t.security.confirmRegenBackup}
            onConfirm={() => regenBackup.mutate()}
          >
            <Button>{t.security.regenBackup}</Button>
          </Popconfirm>
        }
        loading={isLoading}
      >
        <Paragraph type="secondary">{t.security.backupCodesDesc}</Paragraph>
        <Tag color={status && status.backup_codes_remaining > 0 ? "green" : "default"}>
          {status?.backup_codes_remaining ?? 0} {t.security.remaining}
        </Tag>
      </Card>

      {/* TOTP setup 모달 */}
      <Modal
        open={totpModal.open}
        title={t.security.setupTotpTitle}
        onCancel={() => setTotpModal({ open: false })}
        onOk={() => verifyTotp.mutate(totpCode)}
        okText={t.security.verify}
        confirmLoading={verifyTotp.isPending}
        okButtonProps={{ disabled: !/^\d{6,8}$/.test(totpCode) }}
      >
        <Paragraph type="secondary">{t.security.setupTotpDesc}</Paragraph>
        {totpModal.qr && (
          <div style={{ textAlign: "center", margin: "12px 0" }}>
            <img
              src={`data:image/png;base64,${totpModal.qr}`}
              alt="TOTP QR"
              style={{ width: 200, height: 200, background: "#fff", padding: 8, borderRadius: 8 }}
            />
          </div>
        )}
        {totpModal.secret && (
          <Text type="secondary" copyable={{ text: totpModal.secret }} style={{ fontFamily: "monospace", fontSize: 12 }}>
            {t.security.totpSecret}: {totpModal.secret}
          </Text>
        )}
        <Form layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item label={t.security.enterTotpCode}>
            <Input
              autoFocus
              placeholder="123 456"
              value={totpCode}
              onChange={(e) => setTotpCode(e.target.value.replace(/\D/g, ""))}
              maxLength={8}
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* 백업 코드 1회 노출 모달 */}
      <Modal
        open={!!backupCodes}
        title={t.security.backupCodesTitle}
        onOk={() => setBackupCodes(null)}
        onCancel={() => setBackupCodes(null)}
        okText={t.security.savedIt}
        cancelButtonProps={{ style: { display: "none" } }}
      >
        <Alert
          showIcon
          type="warning"
          message={t.security.backupCodesWarn}
          style={{ marginBottom: 12 }}
        />
        <pre
          style={{
            background: "rgba(255,255,255,0.05)",
            padding: 12,
            borderRadius: 8,
            fontFamily: "monospace",
            fontSize: 13,
            lineHeight: 1.8,
            margin: 0,
          }}
        >
          {(backupCodes ?? []).join("\n")}
        </pre>
      </Modal>

      {/* ── Personal Webhook Tokens ─────────────────────────── */}
      <PersonalWebhookTokensCard />

      {/* ── 역할 변경 요청 ───────────────────────────────────── */}
      <RoleChangeRequestCard />
    </div>
  );
}

// ── Personal Webhook Tokens 카드 ─────────────────────────────────
function PersonalWebhookTokensCard() {
  const { locale } = useI18n();
  const qc = useQueryClient();
  const { data: tokens } = useQuery({ queryKey: ["webhook-tokens"], queryFn: webhookTokensApi.list });
  const { data: assets } = useQuery({
    queryKey: ["assets-lite-webhook"],
    queryFn: async () => {
      const { data } = await api.get<Page<Asset>>("/assets", { params: { limit: 200 } });
      return data.items;
    },
  });

  const [issueOpen, setIssueOpen] = useState(false);
  const [tokenName, setTokenName] = useState("");
  const [created, setCreated] = useState<WebhookTokenCreated | null>(null);
  const [snippetAsset, setSnippetAsset] = useState<number | null>(null);
  const [snippet, setSnippet] = useState<{ gh: string; gl: string; name: string } | null>(null);

  const issue = useMutation({
    mutationFn: (name: string) => webhookTokensApi.create(name),
    onSuccess: (data) => {
      setCreated(data);
      setIssueOpen(false);
      setTokenName("");
      qc.invalidateQueries({ queryKey: ["webhook-tokens"] });
    },
    onError: (e: Error & { response?: { data?: { detail?: string } } }) => {
      message.error(e.response?.data?.detail ?? e.message);
    },
  });

  const revoke = useMutation({
    mutationFn: (id: number) => webhookTokensApi.revoke(id),
    onSuccess: () => {
      message.success(locale === "ko" ? "회수됨" : "Revoked");
      qc.invalidateQueries({ queryKey: ["webhook-tokens"] });
    },
  });

  const loadSnippet = useMutation({
    mutationFn: (assetId: number) => webhookTokensApi.snippet(assetId),
    onSuccess: (data) => {
      setSnippet({ gh: data.github_actions, gl: data.gitlab_ci, name: data.asset_name });
    },
  });

  const active = (tokens ?? []).filter((t) => !t.revoked_at);

  return (
    <Card
      title={
        <Space>
          <ApiOutlined />
          <span>{locale === "ko" ? "Personal Webhook Tokens" : "Personal Webhook Tokens"}</span>
          {active.length > 0 && <Tag color="green">{active.length}</Tag>}
        </Space>
      }
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setIssueOpen(true)}>
          {locale === "ko" ? "토큰 발급" : "Issue token"}
        </Button>
      }
      style={{ marginTop: 16 }}
    >
      <Paragraph type="secondary">
        {locale === "ko"
          ? "사내 CI/CD가 사용자 세션 없이 Mond에 스캔을 트리거할 수 있게 발급. raw 토큰은 발급 직후 한 번만 노출됩니다."
          : "Issue tokens so CI/CD can trigger scans without a user session. Raw token is shown only once."}
      </Paragraph>

      {(tokens ?? []).length === 0 ? (
        <Empty description={locale === "ko" ? "발급된 토큰이 없습니다" : "No tokens"} />
      ) : (
        <Table
          size="small"
          pagination={false}
          dataSource={tokens ?? []}
          rowKey="id"
          columns={[
            { title: locale === "ko" ? "라벨" : "Label", dataIndex: "name" },
            {
              title: locale === "ko" ? "토큰" : "Token",
              dataIndex: "token_prefix",
              render: (v: string) => <code className="mond-mono">{v}••••</code>,
              width: 200,
            },
            {
              title: locale === "ko" ? "최근 사용" : "Last used",
              dataIndex: "last_used_at",
              render: (v: string | null) => v ? v.slice(0, 19).replace("T", " ") : "—",
              width: 180,
            },
            {
              title: locale === "ko" ? "상태" : "Status",
              dataIndex: "revoked_at",
              render: (v: string | null) =>
                v ? <Tag color="default">{locale === "ko" ? "회수됨" : "Revoked"}</Tag>
                  : <Tag color="green">{locale === "ko" ? "활성" : "Active"}</Tag>,
              width: 100,
            },
            {
              title: "",
              width: 60,
              render: (_: unknown, r: WebhookTokenRow) =>
                r.revoked_at ? null : (
                  <Popconfirm
                    title={locale === "ko" ? "이 토큰을 회수할까요?" : "Revoke this token?"}
                    okType="danger"
                    onConfirm={() => revoke.mutate(r.id)}
                  >
                    <Button size="small" type="text" danger icon={<DeleteOutlined />} />
                  </Popconfirm>
                ),
            },
          ]}
        />
      )}

      {/* 발급 직후 raw 노출 모달 */}
      <Modal
        open={!!created}
        title={locale === "ko" ? "토큰 발급됨 — 한 번만 표시됩니다" : "Token issued — shown only once"}
        onOk={() => setCreated(null)}
        onCancel={() => setCreated(null)}
        okText={locale === "ko" ? "저장했어요" : "I saved it"}
        cancelButtonProps={{ style: { display: "none" } }}
      >
        <Alert
          type="warning"
          showIcon
          message={
            locale === "ko"
              ? "이 토큰은 다시 표시되지 않습니다. CI 시크릿에 즉시 등록하세요."
              : "This token will not be shown again. Save it to CI secrets immediately."
          }
          style={{ marginBottom: 12 }}
        />
        <Input.TextArea
          value={created?.raw_token ?? ""}
          rows={2}
          readOnly
          style={{ fontFamily: "monospace" }}
        />
        <Button
          icon={<CopyOutlined />}
          style={{ marginTop: 8 }}
          onClick={async () => {
            await navigator.clipboard.writeText(created?.raw_token ?? "");
            message.success(locale === "ko" ? "클립보드에 복사됨" : "Copied");
          }}
        >
          {locale === "ko" ? "복사" : "Copy"}
        </Button>
      </Modal>

      {/* 발급 폼 */}
      <Modal
        open={issueOpen}
        title={locale === "ko" ? "Webhook 토큰 발급" : "Issue webhook token"}
        onOk={() => issue.mutate(tokenName.trim() || "CI token")}
        onCancel={() => setIssueOpen(false)}
        confirmLoading={issue.isPending}
        okText={locale === "ko" ? "발급" : "Issue"}
      >
        <Paragraph type="secondary">
          {locale === "ko"
            ? "이 토큰을 어디에 사용할지 알아볼 수 있게 라벨을 적어 주세요."
            : "Give the token a label so you remember where it's used."}
        </Paragraph>
        <Input
          autoFocus
          value={tokenName}
          onChange={(e) => setTokenName(e.target.value)}
          placeholder="GitHub Actions · main repo"
          maxLength={120}
        />
      </Modal>

      {/* CI YAML 스니펫 발급기 */}
      <div style={{ marginTop: 16, padding: 12, background: "var(--mond-surface-2)", borderRadius: 8 }}>
        <Space direction="vertical" style={{ width: "100%" }}>
          <Text strong>
            {locale === "ko" ? "CI/CD 스니펫 생성" : "Generate CI/CD snippet"}
          </Text>
          <Paragraph type="secondary" style={{ marginBottom: 4 }}>
            {locale === "ko"
              ? "자산을 선택하면 GitHub Actions와 GitLab CI에 그대로 붙여넣을 수 있는 YAML이 생성됩니다."
              : "Pick an asset to get drop-in YAML for GitHub Actions and GitLab CI."}
          </Paragraph>
          <Space>
            <Select
              showSearch
              optionFilterProp="label"
              placeholder={locale === "ko" ? "자산 선택" : "Pick an asset"}
              value={snippetAsset ?? undefined}
              onChange={setSnippetAsset}
              style={{ width: 360 }}
              options={(assets ?? []).map((a) => ({
                value: a.id,
                label: `${a.name} (${a.asset_type})`,
              }))}
            />
            <Button
              type="primary"
              disabled={!snippetAsset}
              onClick={() => snippetAsset && loadSnippet.mutate(snippetAsset)}
              loading={loadSnippet.isPending}
            >
              {locale === "ko" ? "스니펫 생성" : "Generate"}
            </Button>
          </Space>
        </Space>
      </div>

      <Modal
        open={!!snippet}
        onCancel={() => setSnippet(null)}
        onOk={() => setSnippet(null)}
        okText={locale === "ko" ? "닫기" : "Close"}
        cancelButtonProps={{ style: { display: "none" } }}
        width={720}
        title={
          locale === "ko"
            ? `"${snippet?.name}" — CI/CD 스니펫`
            : `"${snippet?.name}" — CI/CD snippet`
        }
      >
        <Alert
          type="info"
          showIcon
          style={{ marginBottom: 12 }}
          message={
            locale === "ko"
              ? "CI Secrets에 MOND_WEBHOOK_TOKEN(raw 토큰) + MOND_HOST(예: mond.your-corp.com) 두 개를 먼저 등록하세요."
              : "Register MOND_WEBHOOK_TOKEN (raw token) and MOND_HOST in your CI secrets first."
          }
        />
        {snippet && (
          <Space direction="vertical" style={{ width: "100%" }} size="middle">
            <SnippetBlock label="GitHub Actions" content={snippet.gh} />
            <SnippetBlock label="GitLab CI" content={snippet.gl} />
          </Space>
        )}
      </Modal>
    </Card>
  );
}

function SnippetBlock({ label, content }: { label: string; content: string }) {
  return (
    <div>
      <Space style={{ marginBottom: 6 }}>
        <Text strong>{label}</Text>
        <Button
          size="small"
          icon={<CopyOutlined />}
          onClick={async () => {
            await navigator.clipboard.writeText(content);
            message.success("Copied");
          }}
        >
          Copy
        </Button>
      </Space>
      <pre
        className="mond-mono"
        style={{
          background: "var(--mond-surface-0)",
          padding: 12,
          borderRadius: 8,
          fontSize: 12,
          margin: 0,
          whiteSpace: "pre-wrap",
        }}
      >
        {content}
      </pre>
    </div>
  );
}

// ── 역할 변경 요청 카드 ──────────────────────────────────────────
const ROLE_OPTIONS: { value: Role; label: string }[] = [
  { value: "viewer", label: "VIEWER" },
  { value: "employee", label: "EMPLOYEE" },
  { value: "reviewer", label: "REVIEWER" },
  { value: "admin", label: "ADMIN" },
];

function RoleChangeRequestCard() {
  const { locale } = useI18n();
  const { user } = useAuth();
  const qc = useQueryClient();
  const { data: history } = useQuery({
    queryKey: ["role-requests-mine"],
    queryFn: roleRequestsApi.myList,
  });
  const [toRole, setToRole] = useState<Role | undefined>(undefined);
  const [reason, setReason] = useState("");

  const submit = useMutation({
    mutationFn: () => roleRequestsApi.request(toRole as Role, reason.trim()),
    onSuccess: (r) => {
      message.success(
        r.status === "ai_auto_approved"
          ? locale === "ko" ? "자동 승인되어 즉시 적용되었습니다." : "Auto-approved and applied."
          : locale === "ko" ? "검토 대기열에 등록되었습니다." : "Submitted for review.",
      );
      setReason("");
      setToRole(undefined);
      qc.invalidateQueries({ queryKey: ["role-requests-mine"] });
    },
    onError: (e: Error & { response?: { data?: { detail?: string } } }) => {
      message.error(e.response?.data?.detail ?? e.message);
    },
  });

  const statusColor = (s: RoleRequestRow["status"]) =>
    s === "approved" || s === "ai_auto_approved"
      ? "green"
      : s === "denied"
        ? "red"
        : s === "needs_human_review"
          ? "orange"
          : "default";

  return (
    <Card
      title={
        <Space>
          <TeamOutlined />
          <span>{locale === "ko" ? "역할 변경 요청" : "Role change request"}</span>
          {user && (
            <Tag color="purple">
              {locale === "ko" ? "현재" : "Current"}: {user.role.toUpperCase()}
            </Tag>
          )}
        </Space>
      }
      style={{ marginTop: 16 }}
    >
      <Paragraph type="secondary">
        {locale === "ko"
          ? "보안팀 합류·전배·강등 등 자기 role을 바꿔야 할 때 요청을 보냅니다. AI가 1차 평가하고, 승급은 관리자 검토 대기열로 들어갑니다."
          : "Request a role change. AI evaluates first; promotions go to admin queue, demotions auto-approve."}
      </Paragraph>
      <Space direction="vertical" style={{ width: "100%" }} size="middle">
        <Space style={{ width: "100%" }}>
          <Select
            placeholder={locale === "ko" ? "새 역할" : "New role"}
            value={toRole}
            onChange={setToRole}
            style={{ width: 200 }}
            options={ROLE_OPTIONS.filter((r) => r.value !== user?.role)}
          />
          <Input
            placeholder={locale === "ko" ? "사유 (10자 이상)" : "Reason (min 10 chars)"}
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            style={{ width: 480 }}
            maxLength={2000}
          />
          <Button
            type="primary"
            disabled={!toRole || reason.trim().length < 10}
            loading={submit.isPending}
            onClick={() => submit.mutate()}
          >
            {locale === "ko" ? "요청" : "Request"}
          </Button>
        </Space>

        {(history ?? []).length > 0 && (
          <Table
            size="small"
            pagination={false}
            dataSource={history}
            rowKey="id"
            columns={[
              {
                title: locale === "ko" ? "방향" : "Change",
                render: (_: unknown, r: RoleRequestRow) => (
                  <span>
                    <Tag>{r.from_role.toUpperCase()}</Tag>→<Tag color="purple">{r.to_role.toUpperCase()}</Tag>
                  </span>
                ),
                width: 220,
              },
              { title: locale === "ko" ? "사유" : "Reason", dataIndex: "reason", ellipsis: true },
              {
                title: locale === "ko" ? "상태" : "Status",
                dataIndex: "status",
                render: (s: RoleRequestRow["status"]) => (
                  <Tag color={statusColor(s)}>{s}</Tag>
                ),
                width: 200,
              },
              {
                title: locale === "ko" ? "검토자" : "Reviewer",
                dataIndex: "reviewer_email",
                render: (v: string | null) => v || "—",
                width: 180,
              },
              {
                title: locale === "ko" ? "요청일시" : "Created",
                dataIndex: "created_at",
                render: (v: string) => v.slice(0, 19).replace("T", " "),
                width: 180,
              },
            ]}
          />
        )}
      </Space>
    </Card>
  );
}
