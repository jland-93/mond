/**
 * 자기 역할 변경 요청 — AI 1차 평가 + 관리자 검토. 강등은 자동 승인.
 */

import { TeamOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button, Card, Input, Select, Space, Table, Tag, Typography, message } from "antd";
import { useState } from "react";

import { useAuth } from "@/auth/AuthContext";
import { useI18n } from "@/i18n";
import type { Role } from "@/lib/auth-api";
import { roleRequestsApi, type RoleRequestRow } from "@/lib/role-requests-api";

const { Paragraph } = Typography;

const ROLE_OPTIONS: { value: Role; label: string }[] = [
  { value: "viewer", label: "VIEWER" },
  { value: "employee", label: "EMPLOYEE" },
  { value: "reviewer", label: "REVIEWER" },
  { value: "admin", label: "ADMIN" },
];

export default function RoleChangeRequestCard() {
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
          ? locale === "ko"
            ? "자동 승인되어 즉시 적용되었습니다."
            : "Auto-approved and applied."
          : locale === "ko"
            ? "검토 대기열에 등록되었습니다."
            : "Submitted for review.",
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
                render: (s: RoleRequestRow["status"]) => <Tag color={statusColor(s)}>{s}</Tag>,
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
