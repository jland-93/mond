/**
 * 🌙 Access Review — 보안 담당자가 AI가 담당자 검토로 넘긴 요청을 처리한다
 */

import { CheckOutlined, CloseOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, Button, Card, Form, Input, Modal, Space, Table, Tag, Typography, message } from "antd";
import { useState } from "react";

import { useI18n } from "@/i18n";
import { iamApi, type AccessRequest } from "@/lib/iam-api";

const { Title, Paragraph } = Typography;

const RISK_COLOR: Record<string, string> = {
  critical: "red",
  high: "orange",
  medium: "gold",
  low: "green",
};

export default function AccessReview() {
  const { t } = useI18n();
  const qc = useQueryClient();
  const [decisionFor, setDecisionFor] = useState<{ req: AccessRequest; approve: boolean } | null>(null);
  const [form] = Form.useForm();

  const { data: identities } = useQuery({ queryKey: ["iam-identities"], queryFn: () => iamApi.listIdentities() });
  const { data: permissions } = useQuery({ queryKey: ["iam-permissions"], queryFn: () => iamApi.listPermissions() });
  const { data: queue } = useQuery({
    queryKey: ["access-requests", "needs_human_review"],
    queryFn: () => iamApi.listRequests("needs_human_review"),
  });

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

  return (
    <div>
      <Title level={2} style={{ marginBottom: 8 }}>
        {t.iam.accessReviewTitle}
      </Title>
      <Paragraph type="secondary">{t.iam.accessReviewDesc}</Paragraph>

      <Card style={{ marginTop: 12 }}>
        {(queue ?? []).length === 0 && (
          <Alert
            type="success"
            showIcon
            message={
              t.iam.accessReviewTitle === "Access Review"
                ? "No requests waiting for review."
                : "검토 대기 중인 요청이 없습니다."
            }
          />
        )}
        <Table
          dataSource={queue ?? []}
          rowKey="id"
          size="small"
          pagination={false}
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
              render: (id: number) => permissions?.find((x) => x.id === id)?.name ?? id,
            },
            {
              title: t.iam.aiDecision,
              dataIndex: "ai_decision",
              render: (ai: AccessRequest["ai_decision"]) => (
                <Space direction="vertical" size={2}>
                  <Tag color={RISK_COLOR[ai.risk_level ?? "medium"]}>risk: {ai.risk_level}</Tag>
                  <span style={{ fontSize: 12, color: "var(--mond-text-dim)" }}>{ai.reason}</span>
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
              placeholder={t.iam.accessReviewTitle === "Access Review" ? "Reason" : "결정 이유"}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
