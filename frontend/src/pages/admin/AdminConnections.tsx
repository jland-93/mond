/**
 * 🌙 Admin · Connections — 외부 시스템 연동 통합 관리 (IAM Source · SSO · Webhook)
 */

import { ApiOutlined, CloudOutlined, PlusOutlined, SafetyOutlined, SyncOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  Button,
  Card,
  Col,
  Form,
  Input,
  Modal,
  Row,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from "antd";
import { useState } from "react";

import { useI18n } from "@/i18n";
import { authApi } from "@/lib/auth-api";
import { iamApi, type IAMSource, type IAMSourceKind } from "@/lib/iam-api";

const { Title, Paragraph, Text } = Typography;

const KIND_OPTIONS: IAMSourceKind[] = ["aws", "gcp", "azure", "k8s", "custom"];

export default function AdminConnections() {
  const { t, locale } = useI18n();
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm();

  const { data: sources } = useQuery({ queryKey: ["admin-iam-sources"], queryFn: iamApi.listSources });
  const { data: providers } = useQuery({ queryKey: ["auth-providers"], queryFn: authApi.providers });

  const sync = useMutation({
    mutationFn: (id: number) => iamApi.syncSource(id),
    onSuccess: (data) => {
      message.success(
        `${(data.imported_identities as number) ?? 0} identities · ${
          (data.imported_permissions as number) ?? 0
        } permissions`,
      );
      qc.invalidateQueries({ queryKey: ["admin-iam-sources"] });
      qc.invalidateQueries({ queryKey: ["iam-identities"] });
      qc.invalidateQueries({ queryKey: ["iam-permissions"] });
    },
  });

  const create = useMutation({
    mutationFn: (body: { name: string; kind: IAMSourceKind; config: Record<string, unknown>; credentials_env_ref: Record<string, string> }) =>
      iamApi.createSource(body),
    onSuccess: () => {
      message.success(t.iam.sourceCreated);
      qc.invalidateQueries({ queryKey: ["admin-iam-sources"] });
      setOpen(false);
      form.resetFields();
    },
  });

  return (
    <div>
      <Title level={2} style={{ marginBottom: 8 }}>
        {t.adminArea.connectionsTitle}
      </Title>
      <Paragraph type="secondary">{t.adminArea.connectionsDesc}</Paragraph>

      {/* ── IAM Source ─────────────────────────────────────── */}
      <Card
        title={
          <Space>
            <CloudOutlined />
            <span>{t.adminArea.iamSources}</span>
          </Space>
        }
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setOpen(true)}>
            {t.iam.addSource}
          </Button>
        }
        style={{ marginBottom: 16 }}
      >
        <Table
          dataSource={sources ?? []}
          rowKey="id"
          size="small"
          pagination={false}
          columns={[
            { title: "ID", dataIndex: "id", width: 60 },
            { title: t.common.name, dataIndex: "name" },
            {
              title: t.common.type,
              dataIndex: "kind",
              render: (k: string) => <Tag color="purple">{k.toUpperCase()}</Tag>,
              width: 100,
            },
            { title: "last sync", dataIndex: "last_synced_at_str", render: (v: string | null) => v || "—" },
            {
              title: t.iam.sync,
              render: (_: unknown, r: IAMSource) => (
                <Button size="small" icon={<SyncOutlined />} onClick={() => sync.mutate(r.id)}>
                  {t.iam.syncSource}
                </Button>
              ),
              width: 140,
            },
          ]}
        />
      </Card>

      {/* ── SSO Providers ─────────────────────────────────── */}
      <Card
        title={
          <Space>
            <SafetyOutlined />
            <span>{t.adminArea.ssoTitle}</span>
          </Space>
        }
        style={{ marginBottom: 16 }}
      >
        <Paragraph type="secondary">{t.adminArea.ssoDesc}</Paragraph>
        <Row gutter={[12, 12]}>
          <Col xs={24} md={12}>
            <Card type="inner" title={t.adminArea.ssoMode}>
              <Tag color={providers?.mode === "sso" ? "green" : "orange"}>{providers?.mode ?? "—"}</Tag>
              <Text type="secondary" style={{ marginLeft: 8 }}>
                {providers?.dev_login_enabled
                  ? locale === "ko"
                    ? "Dev Login 활성"
                    : "Dev login enabled"
                  : locale === "ko"
                    ? "Dev Login 비활성"
                    : "Dev login disabled"}
              </Text>
            </Card>
          </Col>
          <Col xs={24} md={12}>
            <Card type="inner" title={t.adminArea.ssoActive}>
              {(providers?.providers ?? []).length === 0 ? (
                <Text type="secondary">
                  {locale === "ko"
                    ? "활성 IdP 없음 — .env에 SSO_PROVIDERS와 해당 ENV를 설정하고 백엔드를 재시작하세요."
                    : "No IdP configured — set SSO_PROVIDERS in .env and restart the backend."}
                </Text>
              ) : (
                <Space wrap>
                  {providers!.providers.map((p) => (
                    <Tag key={p.name} color="geekblue">
                      {p.display}
                    </Tag>
                  ))}
                </Space>
              )}
            </Card>
          </Col>
        </Row>
        <Alert
          style={{ marginTop: 12 }}
          type="info"
          showIcon
          message={t.adminArea.ssoEnvHint}
          description={
            <pre style={{ marginBottom: 0, fontSize: 12 }}>
{`AUTH_MODE=sso
SSO_PROVIDERS=keycloak,okta
SSO_KEYCLOAK_ISSUER=https://kc.example.com/realms/main
SSO_KEYCLOAK_CLIENT_ID=mond
SSO_KEYCLOAK_CLIENT_SECRET=...
SSO_ADMIN_EMAILS=security-lead@example.com`}
            </pre>
          }
        />
      </Card>

      {/* ── Webhook ─────────────────────────────────────── */}
      <Card
        title={
          <Space>
            <ApiOutlined />
            <span>{t.adminArea.webhookTitle}</span>
          </Space>
        }
      >
        <Paragraph type="secondary">{t.adminArea.webhookDesc}</Paragraph>
        <Alert
          type="info"
          showIcon
          message={
            <>
              GitHub Settings → Webhooks →{" "}
              <code>https://&lt;your-mond&gt;/api/v1/webhooks/github</code>
            </>
          }
          description={
            <>
              Content type: <code>application/json</code>. Secret 설정 시 ENV의{" "}
              <code>GITHUB_WEBHOOK_SECRET</code>과 동일하게 맞추세요.
            </>
          }
        />
      </Card>

      <Modal
        title={t.iam.addSource}
        open={open}
        onOk={() => form.submit()}
        onCancel={() => setOpen(false)}
        confirmLoading={create.isPending}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={(values) =>
            create.mutate({
              name: values.name,
              kind: values.kind,
              config: { region: values.region },
              credentials_env_ref: {
                access_key_id: values.access_key_env || "AWS_ACCESS_KEY_ID",
                secret_access_key: values.secret_key_env || "AWS_SECRET_ACCESS_KEY",
              },
            })
          }
        >
          <Form.Item label={t.iam.fields.source} name="name" rules={[{ required: true }]}>
            <Input placeholder="aws-prod" />
          </Form.Item>
          <Form.Item label={t.iam.fields.type} name="kind" rules={[{ required: true }]}>
            <Select options={KIND_OPTIONS.map((k) => ({ value: k, label: k.toUpperCase() }))} />
          </Form.Item>
          <Form.Item label="region" name="region">
            <Input placeholder="us-east-1" />
          </Form.Item>
          <Form.Item label="ENV name for access key" name="access_key_env">
            <Input placeholder="AWS_ACCESS_KEY_ID" />
          </Form.Item>
          <Form.Item label="ENV name for secret key" name="secret_key_env">
            <Input placeholder="AWS_SECRET_ACCESS_KEY" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
