/**
 * IAM Explorer — Identities / Permissions 조회 (read-only).
 * 연동(Source) 추가/동기화는 관리자 모드 → 연동 관리로 분리.
 */

import { CloudDownloadOutlined } from "@ant-design/icons";
import { useQuery } from "@tanstack/react-query";
import { Card, Col, Row, Space, Table, Tag, Typography } from "antd";

import { useI18n } from "@/i18n";
import {
  iamApi,
  type IAMCapability,
  type IAMIdentity,
  type IAMSourceKind,
  type PermissionRow,
} from "@/lib/iam-api";

const { Title, Paragraph } = Typography;

const RISK_COLOR: Record<string, string> = {
  admin: "red",
  write: "orange",
  read: "green",
};

const STATUS_COLOR: Record<IAMCapability["status"], string> = {
  ready: "green",
  demo: "orange",
  coming_soon: "default",
};

const STATUS_LABEL_KO: Record<IAMCapability["status"], string> = {
  ready: "정상 동작",
  demo: "데모 데이터만",
  coming_soon: "곧 지원",
};

const STATUS_LABEL_EN: Record<IAMCapability["status"], string> = {
  ready: "Ready",
  demo: "Demo only",
  coming_soon: "Coming soon",
};

export default function IAMExplorer() {
  const { t, locale } = useI18n();

  const { data: sources } = useQuery({ queryKey: ["iam-sources"], queryFn: iamApi.listSources });
  const { data: identities } = useQuery({ queryKey: ["iam-identities"], queryFn: () => iamApi.listIdentities() });
  const { data: permissions } = useQuery({ queryKey: ["iam-permissions"], queryFn: () => iamApi.listPermissions() });
  const { data: capabilities } = useQuery({ queryKey: ["iam-capabilities"], queryFn: iamApi.capabilities });

  const capByKind = (k: IAMSourceKind): IAMCapability | undefined =>
    (capabilities ?? []).find((c) => c.kind === k);

  return (
    <div>
      <Title level={2} style={{ marginBottom: 8 }}>
        {t.iam.iamExplorerTitle}
      </Title>
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
            {
              title: t.iam.fields.type,
              dataIndex: "kind",
              width: 220,
              render: (k: IAMSourceKind) => {
                const cap = capByKind(k);
                return (
                  <Space size={4} wrap>
                    <Tag>{k.toUpperCase()}</Tag>
                    {cap && (
                      <Tag color={STATUS_COLOR[cap.status]}>
                        {locale === "ko" ? STATUS_LABEL_KO[cap.status] : STATUS_LABEL_EN[cap.status]}
                      </Tag>
                    )}
                  </Space>
                );
              },
            },
            { title: "last sync", dataIndex: "last_synced_at_str", render: (v: string | null) => v || "—" },
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
    </div>
  );
}
