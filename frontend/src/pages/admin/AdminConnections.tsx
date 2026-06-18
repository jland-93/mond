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
import { iamApi, type IAMCapability, type IAMSource, type IAMSourceKind } from "@/lib/iam-api";

const { Title, Paragraph, Text } = Typography;

const KIND_LABEL: Record<IAMSourceKind, string> = {
  aws: "AWS",
  k8s: "Kubernetes",
  ldap: "LDAP / Active Directory (온프레미스)",
  gcp: "Google Cloud",
  azure: "Azure",
  custom: "Custom Webhook",
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

export default function AdminConnections() {
  const { t, locale } = useI18n();
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm();

  const [selectedKind, setSelectedKind] = useState<IAMSourceKind>("aws");

  const { data: sources } = useQuery({ queryKey: ["admin-iam-sources"], queryFn: iamApi.listSources });
  const { data: providers } = useQuery({ queryKey: ["auth-providers"], queryFn: authApi.providers });
  const { data: capabilities } = useQuery({
    queryKey: ["iam-capabilities"],
    queryFn: iamApi.capabilities,
  });
  const capByKind = (k: IAMSourceKind): IAMCapability | undefined =>
    (capabilities ?? []).find((c) => c.kind === k);
  const selectedCap = capByKind(selectedKind);

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
              render: (k: IAMSourceKind) => {
                const cap = capByKind(k);
                return (
                  <Space size={4} wrap>
                    <Tag color="purple">{KIND_LABEL[k] ?? k.toUpperCase()}</Tag>
                    {cap && (
                      <Tag color={STATUS_COLOR[cap.status]}>
                        {locale === "ko" ? STATUS_LABEL_KO[cap.status] : STATUS_LABEL_EN[cap.status]}
                      </Tag>
                    )}
                  </Space>
                );
              },
              width: 240,
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
        width={640}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{ kind: "aws" }}
          onFinish={(v: Record<string, string>) => {
            const k = (v.kind as IAMSourceKind) || "aws";
            let config: Record<string, unknown> = {};
            let credentials_env_ref: Record<string, string> = {};
            if (k === "aws") {
              config = { region: v.region || "us-east-1" };
              credentials_env_ref = {
                access_key_id: v.access_key_env || "AWS_ACCESS_KEY_ID",
                secret_access_key: v.secret_key_env || "AWS_SECRET_ACCESS_KEY",
              };
            } else if (k === "k8s") {
              config = { namespace: v.namespace || "", context: v.context || "" };
              credentials_env_ref = {};
              if (v.kubeconfig_path_env) credentials_env_ref.kubeconfig_path = v.kubeconfig_path_env;
              if (v.kubeconfig_yaml_env) credentials_env_ref.kubeconfig = v.kubeconfig_yaml_env;
            } else if (k === "ldap") {
              config = {
                server: v.server || "ldaps://ad.corp.local",
                base_dn: v.base_dn || "",
                user_base_dn: v.user_base_dn || "",
                group_base_dn: v.group_base_dn || "",
                user_id_attr: v.user_id_attr || "sAMAccountName",
                group_id_attr: v.group_id_attr || "cn",
                member_attr: v.member_attr || "member",
              };
              credentials_env_ref = {
                bind_dn: v.bind_dn_env || "LDAP_BIND_DN",
                bind_password: v.bind_password_env || "LDAP_BIND_PASSWORD",
              };
            } else if (k === "gcp") {
              config = { project_id: v.gcp_project_id || "" };
              credentials_env_ref = {};
              if (v.gcp_credentials_path_env)
                credentials_env_ref.google_application_credentials = v.gcp_credentials_path_env;
              if (v.gcp_credentials_json_env)
                credentials_env_ref.google_credentials_json = v.gcp_credentials_json_env;
            } else if (k === "azure") {
              config = {
                subscription_id: v.azure_subscription_id || "",
                scope: v.azure_scope || "",
              };
              credentials_env_ref = {
                tenant_id: v.azure_tenant_env || "AZURE_TENANT_ID",
                client_id: v.azure_client_id_env || "AZURE_CLIENT_ID",
                client_secret: v.azure_client_secret_env || "AZURE_CLIENT_SECRET",
              };
            }
            create.mutate({ name: v.name, kind: k, config, credentials_env_ref });
          }}
        >
          <Form.Item label={t.iam.fields.source} name="name" rules={[{ required: true }]}>
            <Input placeholder="aws-prod / corp-ad / k8s-staging" />
          </Form.Item>

          <Form.Item label={t.iam.fields.type} name="kind" rules={[{ required: true }]}>
            <Select
              onChange={(v: IAMSourceKind) => setSelectedKind(v)}
              options={(Object.keys(KIND_LABEL) as IAMSourceKind[]).map((k) => {
                const cap = capByKind(k);
                const status = cap?.status ?? "demo";
                const badge = locale === "ko" ? STATUS_LABEL_KO[status] : STATUS_LABEL_EN[status];
                return {
                  value: k,
                  label: (
                    <Space>
                      <span>{KIND_LABEL[k]}</span>
                      <Tag color={STATUS_COLOR[status]} style={{ marginRight: 0 }}>
                        {badge}
                      </Tag>
                    </Space>
                  ),
                };
              })}
            />
          </Form.Item>

          {selectedCap && selectedCap.status !== "ready" && (
            <Alert
              type={selectedCap.status === "coming_soon" ? "warning" : "info"}
              showIcon
              style={{ marginBottom: 16 }}
              message={
                locale === "ko"
                  ? selectedCap.status === "coming_soon"
                    ? "이 유형은 아직 실연동 어댑터가 없습니다. 데모 데이터만 반환됩니다."
                    : "이 유형은 데모 placeholder입니다."
                  : selectedCap.status === "coming_soon"
                    ? "No real adapter yet — only demo data is returned."
                    : "This type is a demo placeholder."
              }
              description={selectedCap.note}
            />
          )}

          {/* AWS */}
          {selectedKind === "aws" && (
            <>
              <Form.Item label="region" name="region">
                <Input placeholder="us-east-1" />
              </Form.Item>
              <Form.Item label="ENV name for access key" name="access_key_env">
                <Input placeholder="AWS_ACCESS_KEY_ID" />
              </Form.Item>
              <Form.Item label="ENV name for secret key" name="secret_key_env">
                <Input placeholder="AWS_SECRET_ACCESS_KEY" />
              </Form.Item>
            </>
          )}

          {/* Kubernetes */}
          {selectedKind === "k8s" && (
            <>
              <Form.Item label="namespace (비우면 전체 클러스터)" name="namespace">
                <Input placeholder="default" />
              </Form.Item>
              <Form.Item label="kubeconfig context (선택)" name="context">
                <Input placeholder="prod-cluster" />
              </Form.Item>
              <Form.Item
                label="ENV name for kubeconfig 파일 경로"
                name="kubeconfig_path_env"
                extra={locale === "ko" ? "예: KUBECONFIG_PATH (in-cluster 실행 시 비워두면 자동 감지)" : "e.g. KUBECONFIG_PATH (leave empty for in-cluster)"}
              >
                <Input placeholder="KUBECONFIG_PATH" />
              </Form.Item>
              <Form.Item label="또는 ENV name for kubeconfig YAML 내용" name="kubeconfig_yaml_env">
                <Input placeholder="KUBECONFIG_YAML" />
              </Form.Item>
            </>
          )}

          {/* LDAP / AD */}
          {selectedKind === "ldap" && (
            <>
              <Form.Item label="LDAP server URI (ldaps:// 권장)" name="server" rules={[{ required: true }]}>
                <Input placeholder="ldaps://ad.corp.local" />
              </Form.Item>
              <Form.Item label="base DN" name="base_dn" rules={[{ required: true }]}>
                <Input placeholder="DC=corp,DC=local" />
              </Form.Item>
              <Form.Item label="user base DN (비우면 base DN)" name="user_base_dn">
                <Input placeholder="CN=Users,DC=corp,DC=local" />
              </Form.Item>
              <Form.Item label="group base DN (비우면 base DN)" name="group_base_dn">
                <Input placeholder="CN=Groups,DC=corp,DC=local" />
              </Form.Item>
              <Form.Item
                label={locale === "ko" ? "사용자 ID 속성 (AD: sAMAccountName · OpenLDAP: uid)" : "User ID attr (AD: sAMAccountName · OpenLDAP: uid)"}
                name="user_id_attr"
              >
                <Input placeholder="sAMAccountName" />
              </Form.Item>
              <Form.Item
                label={locale === "ko" ? "그룹 멤버 속성 (AD: member · OpenLDAP: uniqueMember)" : "Group member attr (AD: member · OpenLDAP: uniqueMember)"}
                name="member_attr"
              >
                <Input placeholder="member" />
              </Form.Item>
              <Form.Item label="ENV name for bind DN" name="bind_dn_env" rules={[{ required: true }]}>
                <Input placeholder="LDAP_BIND_DN" />
              </Form.Item>
              <Form.Item label="ENV name for bind password" name="bind_password_env" rules={[{ required: true }]}>
                <Input placeholder="LDAP_BIND_PASSWORD" />
              </Form.Item>
            </>
          )}

          {/* GCP */}
          {selectedKind === "gcp" && (
            <>
              <Form.Item label="GCP project_id" name="gcp_project_id" rules={[{ required: true }]}>
                <Input placeholder="my-project-123" />
              </Form.Item>
              <Form.Item
                label="ENV name for service account key 파일 경로"
                name="gcp_credentials_path_env"
                extra={locale === "ko" ? "예: GOOGLE_APPLICATION_CREDENTIALS=/secret/sa.json" : "e.g. GOOGLE_APPLICATION_CREDENTIALS=/secret/sa.json"}
              >
                <Input placeholder="GOOGLE_APPLICATION_CREDENTIALS" />
              </Form.Item>
              <Form.Item
                label={locale === "ko" ? "또는 ENV name for service account JSON 내용" : "Or ENV name for SA JSON content"}
                name="gcp_credentials_json_env"
              >
                <Input placeholder="GOOGLE_CREDENTIALS_JSON" />
              </Form.Item>
            </>
          )}

          {/* Azure */}
          {selectedKind === "azure" && (
            <>
              <Form.Item label="Azure subscription_id" name="azure_subscription_id" rules={[{ required: true }]}>
                <Input placeholder="00000000-0000-0000-0000-000000000000" />
              </Form.Item>
              <Form.Item
                label={locale === "ko" ? "scope (선택, 기본 subscription 전체)" : "scope (optional, defaults to whole subscription)"}
                name="azure_scope"
              >
                <Input placeholder="/subscriptions/.../resourceGroups/prod" />
              </Form.Item>
              <Form.Item label="ENV name for tenant_id" name="azure_tenant_env" rules={[{ required: true }]}>
                <Input placeholder="AZURE_TENANT_ID" />
              </Form.Item>
              <Form.Item label="ENV name for client_id" name="azure_client_id_env" rules={[{ required: true }]}>
                <Input placeholder="AZURE_CLIENT_ID" />
              </Form.Item>
              <Form.Item label="ENV name for client_secret" name="azure_client_secret_env" rules={[{ required: true }]}>
                <Input placeholder="AZURE_CLIENT_SECRET" />
              </Form.Item>
            </>
          )}

          {/* Custom */}
          {selectedKind === "custom" && (
            <Text type="secondary">
              {locale === "ko"
                ? "추가 설정 없이 등록할 수 있습니다. 사내 webhook 기반 어댑터는 별도 설계 중입니다."
                : "Can be registered without extra config. In-house webhook adapter is under design."}
            </Text>
          )}
        </Form>
      </Modal>
    </div>
  );
}
