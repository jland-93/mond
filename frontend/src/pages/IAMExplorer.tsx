/**
 * 🌙 IAM Explorer — Identities / Permissions 조회 + Source 동기화
 */

import { CloudDownloadOutlined, PlusOutlined, SyncOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
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
import {
  iamApi,
  type IAMIdentity,
  type IAMSource,
  type IAMSourceKind,
  type PermissionRow,
} from "@/lib/iam-api";

const { Title, Paragraph } = Typography;

const RISK_COLOR: Record<string, string> = {
  admin: "red",
  write: "orange",
  read: "green",
};

const KIND_OPTIONS: IAMSourceKind[] = ["aws", "gcp", "azure", "k8s", "custom"];

export default function IAMExplorer() {
  const { t } = useI18n();
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm();

  const { data: sources } = useQuery({ queryKey: ["iam-sources"], queryFn: iamApi.listSources });
  const { data: identities } = useQuery({ queryKey: ["iam-identities"], queryFn: () => iamApi.listIdentities() });
  const { data: permissions } = useQuery({ queryKey: ["iam-permissions"], queryFn: () => iamApi.listPermissions() });

  const sync = useMutation({
    mutationFn: (id: number) => iamApi.syncSource(id),
    onSuccess: (data) => {
      message.success(
        `${data.imported_identities ?? 0} identities · ${data.imported_permissions ?? 0} permissions`,
      );
      qc.invalidateQueries({ queryKey: ["iam-sources"] });
      qc.invalidateQueries({ queryKey: ["iam-identities"] });
      qc.invalidateQueries({ queryKey: ["iam-permissions"] });
    },
  });

  const create = useMutation({
    mutationFn: (body: { name: string; kind: IAMSourceKind; config: Record<string, unknown>; credentials_env_ref: Record<string, string> }) =>
      iamApi.createSource(body),
    onSuccess: () => {
      message.success("Source 생성됨");
      qc.invalidateQueries({ queryKey: ["iam-sources"] });
      setOpen(false);
      form.resetFields();
    },
  });

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
        <Title level={2} style={{ margin: 0 }}>
          {t.iam.iamExplorerTitle}
        </Title>
        <Space>
          <Button icon={<PlusOutlined />} onClick={() => setOpen(true)}>
            {t.iam.addSource}
          </Button>
        </Space>
      </div>
      <Paragraph type="secondary">{t.iam.iamExplorerDesc}</Paragraph>

      <Card title="Sources" style={{ marginTop: 12 }}>
        <Table
          dataSource={sources ?? []}
          rowKey="id"
          size="small"
          pagination={false}
          columns={[
            { title: "ID", dataIndex: "id", width: 60 },
            { title: t.iam.fields.source, dataIndex: "name" },
            { title: t.iam.fields.type, dataIndex: "kind", render: (k: string) => <Tag>{k.toUpperCase()}</Tag>, width: 100 },
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

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card title="Identities" extra={<Tag icon={<CloudDownloadOutlined />}>{identities?.length ?? 0}</Tag>}>
            <Table
              dataSource={identities ?? []}
              rowKey="id"
              size="small"
              pagination={{ pageSize: 8 }}
              columns={[
                { title: t.iam.fields.identity, dataIndex: "name" },
                {
                  title: t.iam.fields.type,
                  dataIndex: "identity_type",
                  render: (v: IAMIdentity["identity_type"]) => <Tag>{t.iam.identityTypes[v]}</Tag>,
                  width: 110,
                },
                { title: t.iam.fields.externalId, dataIndex: "external_id", ellipsis: true },
              ]}
            />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Permissions" extra={<Tag>{permissions?.length ?? 0}</Tag>}>
            <Table
              dataSource={permissions ?? []}
              rowKey="id"
              size="small"
              pagination={{ pageSize: 8 }}
              columns={[
                { title: t.iam.fields.permission, dataIndex: "name" },
                {
                  title: t.iam.fields.risk,
                  dataIndex: "risk_hint",
                  width: 110,
                  render: (v: PermissionRow["risk_hint"]) =>
                    v ? <Tag color={RISK_COLOR[v] ?? "default"}>{v.toUpperCase()}</Tag> : "—",
                },
                { title: t.iam.fields.externalId, dataIndex: "external_id", ellipsis: true },
              ]}
            />
          </Card>
        </Col>
      </Row>

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
