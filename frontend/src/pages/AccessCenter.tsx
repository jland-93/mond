/**
 * Access Center — 직원이 권한을 요청하고 자기 요청 상태를 본다
 *
 * UX:
 *   1) Source(연동)별로 identity / permission 필터링
 *   2) Identity는 type별 (user / role / service_account / group) 그룹화
 *   3) Permission은 risk_hint를 색·아이콘으로 강조
 *   4) 요청자 이메일은 로그인 사용자로 자동 채움
 *   5) identity + permission + 5자 이상 reason 채워지면 **AI 사전 평가** 미리보기
 *      → 제출 전에 "자동 승인" / "검토 대기" / "거부" 예측을 보여줌
 */

import { CheckCircleFilled, ClockCircleFilled, CloseCircleFilled, SendOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  Button,
  Card,
  Form,
  Input,
  InputNumber,
  Select,
  Space,
  Table,
  Tag,
  Typography,
} from "antd";
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { useAuth } from "@/auth/AuthContext";
import { useI18n } from "@/i18n";
import { api } from "@/lib/api";
import { iamApi, type AccessRequest, type AccessRequestStatus, type IAMIdentity, type IAMSourceKind, type IdentityType, type PermissionRow } from "@/lib/iam-api";
import { identityDisplay, permissionDisplay } from "@/lib/iam-display";

const { Title, Paragraph, Text } = Typography;
const { TextArea } = Input;

const STATUS_COLOR: Record<AccessRequestStatus, string> = {
  pending_ai_review: "blue",
  ai_auto_approved: "green",
  needs_human_review: "orange",
  human_approved: "green",
  human_denied: "red",
  granted: "green",
  grant_failed: "red",
  expired_revoked: "default",
  revoke_failed: "magenta",
};

const RISK_COLOR: Record<string, string> = {
  admin: "red",
  write: "orange",
  read: "green",
  critical: "red",
  high: "orange",
  medium: "gold",
  low: "green",
};

const TYPE_ORDER: IdentityType[] = [
  "user",
  "sso_user",
  "role",
  "service_account",
  "group",
  "sso_group",
];

const TYPE_LABEL: Record<IdentityType, { ko: string; en: string }> = {
  user: { ko: "사용자", en: "Users" },
  role: { ko: "역할", en: "Roles" },
  service_account: { ko: "서비스 계정", en: "Service accounts" },
  group: { ko: "그룹", en: "Groups" },
  sso_user: { ko: "SSO 사용자 (Identity Center 등)", en: "SSO users" },
  sso_group: { ko: "SSO 그룹 (Identity Center 등)", en: "SSO groups" },
};

interface PreviewResp {
  decision: "auto_approve" | "needs_human" | "deny";
  risk_level: string;
  reason: string;
  model: string;
  expected_status: string;
}

function formatRemaining(expiresAt?: string | null, locale: "ko" | "en" = "ko"): string | null {
  if (!expiresAt) return null;
  const ms = new Date(expiresAt).getTime() - Date.now();
  if (ms <= 0) return locale === "ko" ? "만료됨" : "expired";
  const h = Math.floor(ms / 3_600_000);
  const m = Math.floor((ms % 3_600_000) / 60_000);
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

export default function AccessCenter() {
  const { t, locale } = useI18n();
  const { user } = useAuth();
  const qc = useQueryClient();
  const [form] = Form.useForm();

  const { data: sources } = useQuery({ queryKey: ["iam-sources"], queryFn: iamApi.listSources });
  const { data: identities } = useQuery({ queryKey: ["iam-identities"], queryFn: () => iamApi.listIdentities() });
  const { data: permissions } = useQuery({ queryKey: ["iam-permissions"], queryFn: () => iamApi.listPermissions() });
  const { data: requests } = useQuery({ queryKey: ["access-requests"], queryFn: () => iamApi.listRequests() });

  const [sourceFilter, setSourceFilter] = useState<number | null>(null);
  const [identityId, setIdentityId] = useState<number | undefined>(undefined);
  const [permissionId, setPermissionId] = useState<number | undefined>(undefined);
  const [reason, setReason] = useState("");
  const [duration, setDuration] = useState<number | undefined>(8);
  const [preview, setPreview] = useState<PreviewResp | null>(null);
  const [previewing, setPreviewing] = useState(false);

  // 로그인 사용자 이메일을 requester 기본값으로
  useEffect(() => {
    if (user?.email) form.setFieldValue("requester", user.email);
  }, [user, form]);

  // IAM Explorer의 "권한 요청" CTA에서 진입했을 때 URL 파라미터로 사전 채움
  const [searchParams, setSearchParams] = useSearchParams();
  useEffect(() => {
    const pid = Number(searchParams.get("permission_id"));
    const sid = Number(searchParams.get("source_id"));
    const iid = Number(searchParams.get("identity_id"));
    let touched = false;
    if (pid && Number.isFinite(pid)) {
      setPermissionId(pid);
      form.setFieldValue("permission", pid);
      touched = true;
    }
    if (sid && Number.isFinite(sid)) {
      setSourceFilter(sid);
      touched = true;
    }
    if (iid && Number.isFinite(iid)) {
      setIdentityId(iid);
      form.setFieldValue("identity", iid);
      touched = true;
    }
    if (touched) setSearchParams({}, { replace: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Source ID → name/kind 매핑 (Option 안의 소스 태그용)
  const sourceById = useMemo(() => {
    const m = new Map<number, { name: string; kind: IAMSourceKind }>();
    for (const s of sources ?? []) m.set(s.id, { name: s.name, kind: s.kind });
    return m;
  }, [sources]);

  // source 필터에 따른 노출 목록
  const filteredIdentities = useMemo(
    () => (identities ?? []).filter((i) => sourceFilter == null || i.source_id === sourceFilter),
    [identities, sourceFilter],
  );
  const filteredPermissions = useMemo(
    () => (permissions ?? []).filter((p) => sourceFilter == null || p.source_id === sourceFilter),
    [permissions, sourceFilter],
  );

  // Identity OptGroup — IAM Explorer와 같은 헬퍼로 사람이 읽는 이름 + 원본 ID 보조 라인
  const identityGroups = useMemo(() => {
    const map = new Map<IdentityType, IAMIdentity[]>();
    for (const i of filteredIdentities) {
      const arr = map.get(i.identity_type as IdentityType) ?? [];
      arr.push(i);
      map.set(i.identity_type as IdentityType, arr);
    }
    return TYPE_ORDER
      .filter((t) => (map.get(t)?.length ?? 0) > 0)
      .map((t) => ({
        label: TYPE_LABEL[t][locale],
        title: TYPE_LABEL[t][locale],
        options: (map.get(t) ?? []).map((i) => {
          const d = identityDisplay(i);
          const src = sourceById.get(i.source_id);
          const isSso = i.identity_type === "sso_user" || i.identity_type === "sso_group";
          // searchValue로 원본 ID·display_name 모두 매칭 — Select showSearch가 이걸 사용
          const searchValue = [d.primary, d.secondary, i.name, i.external_id]
            .filter(Boolean)
            .join(" ");
          return {
            value: i.id,
            searchValue,
            label: (
              <Space size={6} wrap style={{ width: "100%" }}>
                <Text strong>{d.primary}</Text>
                {isSso && <Tag color="magenta" style={{ marginInlineEnd: 0 }}>SSO</Tag>}
                {src && (
                  <Tag style={{ marginInlineEnd: 0, fontSize: 11 }}>
                    {src.kind.toUpperCase()} · {src.name}
                  </Tag>
                )}
                {d.secondary && (
                  <Text type="secondary" style={{ fontSize: 11, fontFamily: "var(--mond-font-mono, monospace)" }}>
                    {d.secondary}
                  </Text>
                )}
              </Space>
            ),
          };
        }),
      }));
  }, [filteredIdentities, locale, sourceById]);

  // Permission options — 권한 이름 + risk 태그 + 소스 + 설명 + 원본 ARN
  const permissionOptions = useMemo(
    () =>
      filteredPermissions.map((p) => {
        const d = permissionDisplay(p);
        const src = sourceById.get(p.source_id);
        const searchValue = [d.primary, d.secondary, p.name, p.external_id, p.description, p.risk_hint]
          .filter(Boolean)
          .join(" ");
        return {
          value: p.id,
          searchValue,
          label: (
            <Space size={6} wrap style={{ width: "100%" }}>
              <Text strong>{d.primary}</Text>
              {p.risk_hint && (
                <Tag color={RISK_COLOR[p.risk_hint] ?? "default"} style={{ marginInlineEnd: 0 }}>
                  {p.risk_hint.toUpperCase()}
                </Tag>
              )}
              {src && (
                <Tag style={{ marginInlineEnd: 0, fontSize: 11 }}>
                  {src.kind.toUpperCase()} · {src.name}
                </Tag>
              )}
              {p.description && (
                <Text type="secondary" style={{ fontSize: 11 }}>
                  {p.description.length > 60 ? `${p.description.slice(0, 60)}…` : p.description}
                </Text>
              )}
            </Space>
          ),
        };
      }),
    [filteredPermissions, sourceById],
  );

  // 자동 AI 사전 평가 (debounced)
  useEffect(() => {
    if (!identityId || !permissionId || reason.trim().length < 5 || !user?.email) {
      setPreview(null);
      return;
    }
    const timer = setTimeout(async () => {
      setPreviewing(true);
      try {
        const { data } = await api.post<PreviewResp>("/iam/access-requests/preview", {
          requester: user.email,
          reason: reason.trim(),
          target_identity_id: identityId,
          permission_id: permissionId,
          duration_hours: duration,
        });
        setPreview(data);
      } catch {
        setPreview(null);
      } finally {
        setPreviewing(false);
      }
    }, 400);
    return () => clearTimeout(timer);
  }, [identityId, permissionId, reason, duration, user]);

  const submit = useMutation({
    mutationFn: () =>
      iamApi.createRequest({
        requester: user?.email ?? "",
        reason: reason.trim(),
        target_identity_id: identityId!,
        permission_id: permissionId!,
        duration_hours: duration,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["access-requests"] });
      setIdentityId(undefined);
      setPermissionId(undefined);
      setReason("");
      setPreview(null);
      form.resetFields(["identity", "permission", "reason", "duration"]);
      if (user?.email) form.setFieldValue("requester", user.email);
    },
  });

  const selectedPerm = (permissions ?? []).find((p) => p.id === permissionId);

  return (
    <div>
      <Title level={2} style={{ marginBottom: 8 }}>
        {t.iam.accessCenterTitle}
      </Title>
      <Paragraph type="secondary">{t.iam.accessCenterDesc}</Paragraph>

      <Card title={t.iam.submit} style={{ marginTop: 12 }}>
        <Form form={form} layout="vertical" initialValues={{ duration_hours: 8 }}>
          {/* 요청자 — 자동 입력 + 잠금 */}
          <Form.Item label={t.iam.fields.requester} name="requester">
            <Input disabled />
          </Form.Item>

          {/* Source 필터 — 전체 또는 특정 연동 */}
          <Form.Item label={locale === "ko" ? "연동 필터" : "Source filter"}>
            <Select
              placeholder={locale === "ko" ? "전체 연동" : "All sources"}
              allowClear
              value={sourceFilter ?? undefined}
              onChange={(v) => {
                setSourceFilter(v ?? null);
                setIdentityId(undefined);
                setPermissionId(undefined);
                form.setFieldsValue({ identity: undefined, permission: undefined });
              }}
              options={(sources ?? []).map((s) => ({
                value: s.id,
                label: `${s.name} · ${s.kind.toUpperCase()}`,
              }))}
            />
          </Form.Item>

          {/* Identity — type별 OptGroup */}
          <Form.Item
            label={
              <Space>
                <span>{t.iam.fields.identity}</span>
                <Tag>{filteredIdentities.length}</Tag>
              </Space>
            }
            name="identity"
            required
          >
            <Select
              showSearch
              optionFilterProp="searchValue"
              placeholder={locale === "ko" ? "이름·이메일·ARN으로 검색" : "Search by name, email, ARN"}
              value={identityId}
              onChange={setIdentityId}
              options={identityGroups}
            />
          </Form.Item>

          {/* Permission — risk_hint 색 강조 */}
          <Form.Item
            label={
              <Space>
                <span>{t.iam.fields.permission}</span>
                <Tag>{filteredPermissions.length}</Tag>
              </Space>
            }
            name="permission"
            required
          >
            <Select
              showSearch
              optionFilterProp="searchValue"
              placeholder={locale === "ko" ? "권한 이름·ARN·설명 검색" : "Search by name, ARN, description"}
              value={permissionId}
              onChange={setPermissionId}
              options={permissionOptions}
            />
          </Form.Item>

          <Form.Item label={t.iam.fields.duration} name="duration_hours" extra={t.iam.durationHint}>
            <InputNumber
              min={1}
              max={720}
              style={{ width: "100%" }}
              placeholder="8"
              value={duration}
              onChange={(v) => setDuration(v ?? undefined)}
            />
          </Form.Item>

          <Form.Item
            label={t.iam.fields.reason}
            name="reason"
            rules={[{ required: true, min: 5 }]}
          >
            <TextArea
              rows={3}
              placeholder={locale === "ko" ? "이 권한이 왜 필요한지 구체적으로 적어주세요." : "Why do you need this permission?"}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />
          </Form.Item>

          {/* AI 사전 평가 미리보기 */}
          {(previewing || preview) && (
            <Alert
              style={{ marginBottom: 12 }}
              showIcon
              type={
                preview?.decision === "auto_approve"
                  ? "success"
                  : preview?.decision === "deny"
                    ? "error"
                    : "warning"
              }
              icon={
                preview?.decision === "auto_approve" ? <CheckCircleFilled /> :
                preview?.decision === "deny" ? <CloseCircleFilled /> :
                <ClockCircleFilled />
              }
              message={
                <Space>
                  <span>
                    {previewing
                      ? (locale === "ko" ? "AI 평가 중..." : "AI evaluating...")
                      : (locale === "ko" ? "AI 사전 평가" : "AI preview")}
                  </span>
                  {preview && (
                    <>
                      <Tag color={RISK_COLOR[preview.risk_level] || "default"}>
                        risk: {preview.risk_level}
                      </Tag>
                      <Tag>
                        {locale === "ko"
                          ? preview.expected_status === "granted"
                            ? "→ 즉시 승인 예상"
                            : preview.expected_status === "needs_human_review"
                              ? "→ 관리자 검토 필요"
                              : "→ 거부 예상"
                          : `→ ${preview.expected_status}`}
                      </Tag>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {preview.model}
                      </Text>
                    </>
                  )}
                </Space>
              }
              description={preview?.reason}
            />
          )}

          {selectedPerm?.risk_hint === "admin" && (
            <Alert
              type="warning"
              showIcon
              style={{ marginBottom: 12 }}
              message={
                locale === "ko"
                  ? "이 권한은 admin/root 등급입니다. 사유를 가능한 한 구체적으로 작성하세요."
                  : "This is an admin/root-level permission. Describe the reason as specifically as possible."
              }
            />
          )}

          <Button
            type="primary"
            icon={<SendOutlined />}
            loading={submit.isPending}
            disabled={!identityId || !permissionId || reason.trim().length < 5}
            onClick={() => submit.mutate()}
          >
            {t.iam.submit}
          </Button>
        </Form>
      </Card>

      <Card
        title={t.iam.accessCenterTitle === "Access Center" ? "My requests" : "내 요청"}
        style={{ marginTop: 16 }}
      >
        {(requests ?? []).length === 0 && (
          <Alert
            type="info"
            message={t.iam.accessCenterTitle === "Access Center" ? "No requests yet." : "아직 요청이 없습니다."}
          />
        )}
        <Table
          dataSource={requests ?? []}
          rowKey="id"
          size="small"
          expandable={{
            expandedRowRender: (r: AccessRequest) => (
              <Space direction="vertical">
                <div>
                  <Tag color="purple">{t.iam.aiDecision}</Tag>
                  <Tag color={RISK_COLOR[r.ai_decision.risk_level ?? "medium"]}>
                    risk: {r.ai_decision.risk_level ?? "—"}
                  </Tag>
                  {r.ai_decision.decision && (
                    <Tag>
                      {t.iam.decisions[r.ai_decision.decision as keyof typeof t.iam.decisions] ?? r.ai_decision.decision}
                    </Tag>
                  )}
                  <div style={{ marginTop: 6 }}>{r.ai_decision.reason}</div>
                </div>
                {r.human_decision.reviewer && (
                  <div>
                    <Tag color="cyan">{t.iam.humanDecision}</Tag>
                    <Tag color={r.human_decision.approve ? "green" : "red"}>
                      {r.human_decision.approve ? t.iam.approve : t.iam.deny}
                    </Tag>
                    <span style={{ marginLeft: 6 }}>{r.human_decision.reviewer}</span>
                    {r.human_decision.note && <div style={{ marginTop: 4 }}>{r.human_decision.note}</div>}
                  </div>
                )}
                {r.grant_result?.granted_at && (
                  <div>
                    <Tag color="green">{t.iam.grantResult}</Tag>
                    <span>
                      {r.grant_result.success ? "✓" : "✗"}{" "}
                      {String(r.grant_result.detail?.note ?? r.grant_result.detail?.policy_arn ?? "")}
                    </span>
                  </div>
                )}
              </Space>
            ),
          }}
          columns={[
            { title: "#", dataIndex: "id", width: 60 },
            { title: t.iam.fields.requester, dataIndex: "requester" },
            {
              title: t.iam.fields.identity,
              dataIndex: "target_identity_id",
              render: (id: number) => identities?.find((x) => x.id === id)?.name ?? id,
            },
            {
              title: t.iam.fields.permission,
              dataIndex: "permission_id",
              render: (id: number) => {
                const p = permissions?.find((x) => x.id === id);
                if (!p) return id;
                return (
                  <Space size={4}>
                    {p.risk_hint && (
                      <Tag color={RISK_COLOR[p.risk_hint]} style={{ marginRight: 0 }}>
                        {p.risk_hint}
                      </Tag>
                    )}
                    <span>{p.name}</span>
                  </Space>
                );
              },
            },
            {
              title: t.iam.fields.status,
              dataIndex: "status",
              render: (s: AccessRequestStatus) => <Tag color={STATUS_COLOR[s]}>{t.iam.statuses[s]}</Tag>,
              width: 160,
            },
            {
              title: t.iam.expiresIn,
              render: (_: unknown, r: AccessRequest) => {
                if (r.revoked_at) return <Tag>{t.iam.expired}</Tag>;
                const rem = formatRemaining(r.expires_at, locale);
                return rem ? <Tag color="gold">{rem}</Tag> : "—";
              },
              width: 130,
            },
          ]}
        />
      </Card>
    </div>
  );
}
