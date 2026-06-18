/**
 * 🌙 Admin · Users — 사용자 목록 + Role 변경 (ADMIN 전용)
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Avatar, Button, Card, Input, Select, Space, Table, Tabs, Tag, Typography, message } from "antd";
import { CheckOutlined, CloseOutlined, TeamOutlined, UserOutlined } from "@ant-design/icons";
import { useState } from "react";

import { useAuth } from "@/auth/AuthContext";
import { useI18n } from "@/i18n";
import type { Role } from "@/lib/auth-api";
import { roleRequestsApi, type RoleRequestRow } from "@/lib/role-requests-api";
import { usersApi, type AdminUser } from "@/lib/users-api";

const { Title, Paragraph, Text } = Typography;

const ROLES: Role[] = ["viewer", "employee", "reviewer", "admin"];

const ROLE_COLOR: Record<Role, string> = {
  viewer: "default",
  employee: "blue",
  reviewer: "purple",
  admin: "red",
};

export default function AdminUsers() {
  const { t, locale } = useI18n();
  const { user: me } = useAuth();
  const qc = useQueryClient();

  const { data, isLoading } = useQuery({ queryKey: ["admin-users"], queryFn: usersApi.list });

  const updateRole = useMutation({
    mutationFn: ({ id, role }: { id: number; role: Role }) => usersApi.updateRole(id, role),
    onSuccess: () => {
      message.success(locale === "ko" ? "역할 변경됨" : "Role updated");
      qc.invalidateQueries({ queryKey: ["admin-users"] });
    },
    onError: (err: Error & { response?: { data?: { detail?: string } } }) =>
      message.error(err.response?.data?.detail ?? err.message),
  });

  const usersTable = (
    <Card>
      <Table
        loading={isLoading}
        dataSource={data ?? []}
        rowKey="id"
        columns={[
            {
              title: t.adminArea.user,
              render: (_: unknown, u: AdminUser) => (
                <Space>
                  <Avatar size={28} src={u.picture_url ?? undefined} icon={!u.picture_url && <UserOutlined />} />
                  <Space direction="vertical" size={0}>
                    <span>{u.name || u.email}</span>
                    <span style={{ color: "var(--mond-text-dim)", fontSize: 12 }}>{u.email}</span>
                  </Space>
                </Space>
              ),
            },
            {
              title: t.adminArea.ssoProvider,
              dataIndex: "sso_provider",
              render: (v: string | null) => (v ? <Tag>{v}</Tag> : "—"),
              width: 120,
            },
            {
              title: t.adminArea.role,
              dataIndex: "role",
              render: (r: Role, u: AdminUser) => (
                <Select
                  size="small"
                  value={r}
                  style={{ width: 140 }}
                  options={ROLES.map((opt) => ({
                    value: opt,
                    label: (
                      <Tag color={ROLE_COLOR[opt]} style={{ marginRight: 0 }}>
                        {opt.toUpperCase()}
                      </Tag>
                    ),
                  }))}
                  onChange={(val) => updateRole.mutate({ id: u.id, role: val })}
                  disabled={me?.id === u.id && r === "admin"}
                />
              ),
              width: 180,
            },
            {
              title: t.adminArea.lastLogin,
              dataIndex: "last_login_at_iso",
              render: (v: string | null) => (v ? new Date(v).toLocaleString() : "—"),
              width: 200,
          },
        ]}
      />
    </Card>
  );

  return (
    <div>
      <Title level={2} style={{ marginBottom: 8 }}>
        {t.adminArea.usersTitle}
      </Title>
      <Paragraph type="secondary">{t.adminArea.usersDesc}</Paragraph>

      <Tabs
        items={[
          {
            key: "users",
            label: (
              <Space>
                <UserOutlined />
                <span>{locale === "ko" ? "사용자 목록" : "Users"}</span>
                <Tag>{data?.length ?? 0}</Tag>
              </Space>
            ),
            children: usersTable,
          },
          {
            key: "role-requests",
            label: <RoleRequestsTabLabel locale={locale} />,
            children: <RoleRequestsQueue locale={locale} />,
          },
        ]}
      />
    </div>
  );
}

// ── 역할 변경 요청 대기열 ────────────────────────────────────────
function RoleRequestsTabLabel({ locale }: { locale: "ko" | "en" }) {
  const { data } = useQuery({
    queryKey: ["admin-role-requests-pending"],
    queryFn: () => roleRequestsApi.adminList("needs_human_review"),
  });
  return (
    <Space>
      <TeamOutlined />
      <span>{locale === "ko" ? "역할 요청 대기열" : "Role requests"}</span>
      {(data?.length ?? 0) > 0 && <Tag color="orange">{data?.length}</Tag>}
    </Space>
  );
}

function RoleRequestsQueue({ locale }: { locale: "ko" | "en" }) {
  const qc = useQueryClient();
  const [filter, setFilter] = useState<"needs_human_review" | "all">("needs_human_review");
  const { data, isLoading } = useQuery({
    queryKey: ["admin-role-requests", filter],
    queryFn: () =>
      filter === "all" ? roleRequestsApi.adminList() : roleRequestsApi.adminList("needs_human_review"),
  });

  const [noteFor, setNoteFor] = useState<Record<number, string>>({});

  const decide = useMutation({
    mutationFn: (v: { id: number; approve: boolean; note: string }) =>
      roleRequestsApi.decide(v.id, v.approve, v.note),
    onSuccess: (_data, v) => {
      message.success(v.approve
        ? locale === "ko" ? "승인되어 역할이 적용되었습니다" : "Approved and applied"
        : locale === "ko" ? "거부됨" : "Denied",
      );
      qc.invalidateQueries({ queryKey: ["admin-role-requests"] });
      qc.invalidateQueries({ queryKey: ["admin-role-requests-pending"] });
      qc.invalidateQueries({ queryKey: ["admin-users"] });
    },
    onError: (e: Error & { response?: { data?: { detail?: string } } }) =>
      message.error(e.response?.data?.detail ?? e.message),
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
    <Card>
      <Space style={{ marginBottom: 12 }}>
        <span>{locale === "ko" ? "필터" : "Filter"}:</span>
        <Select
          size="small"
          value={filter}
          onChange={(v) => setFilter(v as typeof filter)}
          style={{ width: 200 }}
          options={[
            { value: "needs_human_review", label: locale === "ko" ? "검토 대기" : "Pending" },
            { value: "all", label: locale === "ko" ? "전체" : "All" },
          ]}
        />
      </Space>
      <Table
        loading={isLoading}
        dataSource={data ?? []}
        rowKey="id"
        size="small"
        columns={[
          {
            title: locale === "ko" ? "요청자" : "Requester",
            dataIndex: "requester_email",
            width: 220,
          },
          {
            title: locale === "ko" ? "방향" : "Change",
            render: (_: unknown, r: RoleRequestRow) => (
              <span>
                <Tag>{r.from_role.toUpperCase()}</Tag>→<Tag color="purple">{r.to_role.toUpperCase()}</Tag>
              </span>
            ),
            width: 200,
          },
          { title: locale === "ko" ? "사유" : "Reason", dataIndex: "reason", ellipsis: true },
          {
            title: "AI 평가",
            render: (_: unknown, r: RoleRequestRow) => (
              <Space direction="vertical" size={0}>
                <Tag color={r.ai_decision.risk === "high" ? "red" : r.ai_decision.risk === "medium" ? "orange" : "green"}>
                  {r.ai_decision.decision ?? "—"}
                </Tag>
                <Text type="secondary" style={{ fontSize: 11 }}>
                  {r.ai_decision.reason}
                </Text>
              </Space>
            ),
            width: 240,
          },
          {
            title: locale === "ko" ? "상태" : "Status",
            dataIndex: "status",
            render: (s: RoleRequestRow["status"]) => <Tag color={statusColor(s)}>{s}</Tag>,
            width: 160,
          },
          {
            title: locale === "ko" ? "결정" : "Decision",
            width: 360,
            render: (_: unknown, r: RoleRequestRow) => {
              if (r.status !== "needs_human_review") {
                return (
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {r.reviewer_email ? `${r.reviewer_email}` : "—"}
                    {r.review_note ? ` · ${r.review_note}` : ""}
                  </Text>
                );
              }
              const note = noteFor[r.id] ?? "";
              return (
                <Space.Compact style={{ width: "100%" }}>
                  <Input
                    size="small"
                    placeholder={locale === "ko" ? "메모 (선택)" : "Note (optional)"}
                    value={note}
                    onChange={(e) => setNoteFor({ ...noteFor, [r.id]: e.target.value })}
                  />
                  <Button
                    size="small"
                    type="primary"
                    icon={<CheckOutlined />}
                    loading={decide.isPending && decide.variables?.id === r.id && decide.variables.approve}
                    onClick={() => decide.mutate({ id: r.id, approve: true, note })}
                  >
                    {locale === "ko" ? "승인" : "Approve"}
                  </Button>
                  <Button
                    size="small"
                    danger
                    icon={<CloseOutlined />}
                    loading={decide.isPending && decide.variables?.id === r.id && !decide.variables.approve}
                    onClick={() => decide.mutate({ id: r.id, approve: false, note })}
                  >
                    {locale === "ko" ? "거부" : "Deny"}
                  </Button>
                </Space.Compact>
              );
            },
          },
        ]}
      />
    </Card>
  );
}

