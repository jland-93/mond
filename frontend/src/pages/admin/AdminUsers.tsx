/**
 * 🌙 Admin · Users — 사용자 목록 + Role 변경 (ADMIN 전용)
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Avatar, Card, Select, Space, Table, Tag, Typography, message } from "antd";
import { UserOutlined } from "@ant-design/icons";

import { useAuth } from "@/auth/AuthContext";
import { useI18n } from "@/i18n";
import type { Role } from "@/lib/auth-api";
import { usersApi, type AdminUser } from "@/lib/users-api";

const { Title, Paragraph } = Typography;

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

  return (
    <div>
      <Title level={2} style={{ marginBottom: 8 }}>
        {t.adminArea.usersTitle}
      </Title>
      <Paragraph type="secondary">{t.adminArea.usersDesc}</Paragraph>

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
    </div>
  );
}
