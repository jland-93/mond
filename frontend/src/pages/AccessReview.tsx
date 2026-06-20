/**
 * Access Review — 보안 담당자가 AI 1차 검토를 통과 못한 요청을 처리한다.
 *
 * 가시화 원칙:
 *   - identity / permission은 readable name + 원본 ID(monospace 보조)
 *   - AI 결정(verdict + risk + reason)을 카드처럼 강조
 *   - critical / high 위험은 행 좌측 색띠로 즉시 인지
 */

import {
  CheckOutlined,
  ClockCircleOutlined,
  CloseOutlined,
  RobotOutlined,
} from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  Button,
  Card,
  Empty,
  Form,
  Input,
  Modal,
  Space,
  Table,
  Tag,
  Tooltip,
  Typography,
  message,
} from "antd";
import { useMemo, useState } from "react";

import { useI18n } from "@/i18n";
import { iamApi, type AccessRequest, type IAMSourceKind } from "@/lib/iam-api";
import { identityDisplay, permissionDisplay } from "@/lib/iam-display";

const { Title, Paragraph, Text } = Typography;

const RISK_COLOR: Record<string, string> = {
  critical: "red",
  high: "orange",
  medium: "gold",
  low: "green",
};

const DECISION_COLOR: Record<string, string> = {
  auto_approve: "green",
  needs_human: "gold",
  deny: "red",
};

export default function AccessReview() {
  const { t, locale } = useI18n();
  const qc = useQueryClient();
  const [decisionFor, setDecisionFor] = useState<{ req: AccessRequest; approve: boolean } | null>(null);
  const [form] = Form.useForm();

  const { data: sources } = useQuery({ queryKey: ["iam-sources"], queryFn: iamApi.listSources });
  const { data: identities } = useQuery({
    queryKey: ["iam-identities"],
    queryFn: () => iamApi.listIdentities(),
  });
  const { data: permissions } = useQuery({
    queryKey: ["iam-permissions"],
    queryFn: () => iamApi.listPermissions(),
  });
  const { data: queue } = useQuery({
    queryKey: ["access-requests", "needs_human_review"],
    queryFn: () => iamApi.listRequests("needs_human_review"),
  });

  const sourceById = useMemo(() => {
    const m = new Map<number, { name: string; kind: IAMSourceKind }>();
    for (const s of sources ?? []) m.set(s.id, { name: s.name, kind: s.kind });
    return m;
  }, [sources]);

  const decide = useMutation({
    mutationFn: ({ id, approve, reviewer, note }: { id: number; approve: boolean; reviewer: string; note?: string }) =>
      iamApi.humanDecision(id, { approve, reviewer, note }),
    onSuccess: () => {
      message.success(t.iam.decisionApplied);
      qc.invalidateQueries({ queryKey: ["access-requests"] });
      setDecisionFor(null);
      form.resetFields();
    },
  });

  const sweep = useMutation({
    mutationFn: () => iamApi.sweepExpired(),
    onSuccess: (data) => {
      message.success(`${t.iam.sweepDone} (${data.revoked})`);
      qc.invalidateQueries({ queryKey: ["access-requests"] });
    },
  });

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
        <Title level={2} style={{ margin: 0 }}>
          {t.iam.accessReviewTitle}
        </Title>
        <Button
          icon={<ClockCircleOutlined />}
          loading={sweep.isPending}
          onClick={() => sweep.mutate()}
        >
          {t.iam.sweepExpired}
        </Button>
      </div>
      <Paragraph type="secondary">{t.iam.accessReviewDesc}</Paragraph>

      <Card style={{ marginTop: 12 }}>
        {(queue ?? []).length === 0 ? (
          <Empty
            description={
              <Space direction="vertical" align="center" size={4}>
                <Text strong>
                  {locale === "ko" ? "검토 대기 중인 요청이 없습니다" : "No requests waiting for review"}
                </Text>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {locale === "ko"
                    ? "AI가 자동 승인했거나 위험이 낮아 사람 검토가 불필요했던 건들은 권한 요청 페이지의 '내 요청' 또는 감사 로그에서 볼 수 있습니다."
                    : "Items auto-approved by AI or low-risk requests are visible under '내 요청' or the audit log."}
                </Text>
              </Space>
            }
          />
        ) : (
          <Alert
            type="warning"
            showIcon
            style={{ marginBottom: 12 }}
            message={
              locale === "ko"
                ? `${(queue ?? []).length}건이 사람 검토를 기다리고 있습니다. AI가 자동 결정하지 못한 회색지대 — 사유와 위험도를 확인하고 승인/거부하세요.`
                : `${(queue ?? []).length} request(s) are waiting for human review.`
            }
          />
        )}

        <Table
          dataSource={queue ?? []}
          rowKey="id"
          size="small"
          pagination={false}
          rowClassName={(r) => {
            const risk = r.ai_decision.risk_level;
            if (risk === "critical") return "mond-row-critical";
            if (risk === "high") return "mond-row-high";
            return "";
          }}
          columns={[
            { title: "#", dataIndex: "id", width: 60 },
            { title: t.iam.fields.requester, dataIndex: "requester", width: 200 },
            {
              title: t.iam.fields.identity,
              dataIndex: "target_identity_id",
              render: (id: number) => {
                const i = identities?.find((x) => x.id === id);
                if (!i) return id;
                const d = identityDisplay(i);
                const src = sourceById.get(i.source_id);
                const isSso = i.identity_type === "sso_user" || i.identity_type === "sso_group";
                return (
                  <Space direction="vertical" size={0}>
                    <Space size={4} wrap>
                      <Tooltip title={d.tooltip}>
                        <Text strong>{d.primary}</Text>
                      </Tooltip>
                      {isSso && <Tag color="magenta" style={{ marginInlineEnd: 0 }}>SSO</Tag>}
                      {src && <Tag style={{ marginInlineEnd: 0, fontSize: 11 }}>{src.kind.toUpperCase()}</Tag>}
                    </Space>
                    {d.secondary && (
                      <Text type="secondary" style={{ fontSize: 11, fontFamily: "var(--mond-font-mono, monospace)" }} ellipsis>
                        {d.secondary}
                      </Text>
                    )}
                  </Space>
                );
              },
            },
            {
              title: t.iam.fields.permission,
              dataIndex: "permission_id",
              render: (id: number) => {
                const p = permissions?.find((x) => x.id === id);
                if (!p) return id;
                const d = permissionDisplay(p);
                const src = sourceById.get(p.source_id);
                return (
                  <Space direction="vertical" size={0}>
                    <Space size={4} wrap>
                      <Tooltip title={d.tooltip}>
                        <Text strong>{d.primary}</Text>
                      </Tooltip>
                      {p.risk_hint && (
                        <Tag color={RISK_COLOR[p.risk_hint] ?? "default"} style={{ marginInlineEnd: 0 }}>
                          {p.risk_hint.toUpperCase()}
                        </Tag>
                      )}
                      {src && <Tag style={{ marginInlineEnd: 0, fontSize: 11 }}>{src.kind.toUpperCase()}</Tag>}
                    </Space>
                    {p.description && (
                      <Text type="secondary" style={{ fontSize: 11 }} ellipsis>
                        {p.description}
                      </Text>
                    )}
                  </Space>
                );
              },
            },
            {
              title: (
                <Space size={4}>
                  <RobotOutlined />
                  <span>{t.iam.aiDecision}</span>
                </Space>
              ),
              dataIndex: "ai_decision",
              width: 240,
              render: (ai: AccessRequest["ai_decision"]) => (
                <Space direction="vertical" size={2} style={{ width: "100%" }}>
                  <Space size={4} wrap>
                    {ai.decision && (
                      <Tag color={DECISION_COLOR[ai.decision as string] ?? "default"} style={{ marginInlineEnd: 0 }}>
                        {t.iam.decisions[ai.decision as keyof typeof t.iam.decisions] ?? ai.decision}
                      </Tag>
                    )}
                    {ai.risk_level && (
                      <Tag color={RISK_COLOR[ai.risk_level as string] ?? "default"} style={{ marginInlineEnd: 0 }}>
                        {locale === "ko" ? "위험도" : "risk"}:{" "}
                        {(t.iam.riskLevels as Record<string, string>)[ai.risk_level as string] ?? ai.risk_level}
                      </Tag>
                    )}
                  </Space>
                  {ai.reason && (
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {ai.reason}
                    </Text>
                  )}
                </Space>
              ),
            },
            { title: t.iam.fields.reason, dataIndex: "reason", ellipsis: true },
            {
              title: t.iam.fields.decision,
              render: (_: unknown, r: AccessRequest) => (
                <Space>
                  <Button
                    size="small"
                    type="primary"
                    icon={<CheckOutlined />}
                    onClick={() => setDecisionFor({ req: r, approve: true })}
                  >
                    {t.iam.approve}
                  </Button>
                  <Button
                    size="small"
                    danger
                    icon={<CloseOutlined />}
                    onClick={() => setDecisionFor({ req: r, approve: false })}
                  >
                    {t.iam.deny}
                  </Button>
                </Space>
              ),
              width: 200,
            },
          ]}
        />
      </Card>

      <Modal
        title={`${decisionFor?.approve ? t.iam.approve : t.iam.deny} — #${decisionFor?.req.id}`}
        open={!!decisionFor}
        onCancel={() => setDecisionFor(null)}
        onOk={() => form.submit()}
        confirmLoading={decide.isPending}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={(v) =>
            decisionFor &&
            decide.mutate({
              id: decisionFor.req.id,
              approve: decisionFor.approve,
              reviewer: v.reviewer,
              note: v.note,
            })
          }
        >
          <Form.Item label={t.iam.fields.reviewer} name="reviewer" rules={[{ required: true }]}>
            <Input placeholder="security-team@example.com" />
          </Form.Item>
          <Form.Item label={t.iam.fields.note} name="note">
            <Input.TextArea
              rows={3}
              placeholder={locale === "ko" ? "결정 이유" : "Reason"}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
