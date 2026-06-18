/**
 * IAM Source 추가 modal — kind 선택에 따라 5종 form fields가 전환된다.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, Form, Input, Modal, Select, Space, Tag, Typography, message } from "antd";
import { useState } from "react";

import { useI18n } from "@/i18n";
import { iamApi, type IAMCapability, type IAMSourceKind } from "@/lib/iam-api";

import { KIND_LABEL, STATUS_COLOR, STATUS_LABEL_EN, STATUS_LABEL_KO } from "./constants";

const { Text } = Typography;

interface Props {
  open: boolean;
  onClose: () => void;
}

export default function IAMSourceModal({ open, onClose }: Props) {
  const { t, locale } = useI18n();
  const qc = useQueryClient();
  const [form] = Form.useForm();
  const [selectedKind, setSelectedKind] = useState<IAMSourceKind>("aws");

  const { data: capabilities } = useQuery({ queryKey: ["iam-capabilities"], queryFn: iamApi.capabilities });
  const capByKind = (k: IAMSourceKind): IAMCapability | undefined =>
    (capabilities ?? []).find((c) => c.kind === k);
  const selectedCap = capByKind(selectedKind);

  const create = useMutation({
    mutationFn: (body: {
      name: string;
      kind: IAMSourceKind;
      config: Record<string, unknown>;
      credentials_env_ref: Record<string, string>;
    }) => iamApi.createSource(body),
    onSuccess: () => {
      message.success(t.iam.sourceCreated);
      qc.invalidateQueries({ queryKey: ["admin-iam-sources"] });
      onClose();
      form.resetFields();
    },
  });

  return (
    <Modal
      title={t.iam.addSource}
      open={open}
      onOk={() => form.submit()}
      onCancel={onClose}
      confirmLoading={create.isPending}
      width={640}
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{ kind: "aws" }}
        onFinish={(v: Record<string, string>) => create.mutate(toCreateBody(v))}
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

        {selectedKind === "aws" && <AWSFields />}
        {selectedKind === "k8s" && <K8sFields />}
        {selectedKind === "ldap" && <LDAPFields locale={locale} />}
        {selectedKind === "gcp" && <GCPFields locale={locale} />}
        {selectedKind === "azure" && <AzureFields locale={locale} />}
        {selectedKind === "custom" && (
          <Text type="secondary">
            {locale === "ko"
              ? "추가 설정 없이 등록할 수 있습니다. 사내 webhook 기반 어댑터는 별도 설계 중입니다."
              : "Can be registered without extra config. In-house webhook adapter is under design."}
          </Text>
        )}
      </Form>
    </Modal>
  );
}

function toCreateBody(v: Record<string, string>) {
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

  return { name: v.name, kind: k, config, credentials_env_ref };
}

function AWSFields() {
  return (
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
  );
}

function K8sFields() {
  const { locale } = useI18n();
  return (
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
        extra={
          locale === "ko"
            ? "예: KUBECONFIG_PATH (in-cluster 실행 시 비워두면 자동 감지)"
            : "e.g. KUBECONFIG_PATH (leave empty for in-cluster)"
        }
      >
        <Input placeholder="KUBECONFIG_PATH" />
      </Form.Item>
      <Form.Item label="또는 ENV name for kubeconfig YAML 내용" name="kubeconfig_yaml_env">
        <Input placeholder="KUBECONFIG_YAML" />
      </Form.Item>
    </>
  );
}

function LDAPFields({ locale }: { locale: "ko" | "en" }) {
  return (
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
        label={
          locale === "ko"
            ? "사용자 ID 속성 (AD: sAMAccountName · OpenLDAP: uid)"
            : "User ID attr (AD: sAMAccountName · OpenLDAP: uid)"
        }
        name="user_id_attr"
      >
        <Input placeholder="sAMAccountName" />
      </Form.Item>
      <Form.Item
        label={
          locale === "ko"
            ? "그룹 멤버 속성 (AD: member · OpenLDAP: uniqueMember)"
            : "Group member attr (AD: member · OpenLDAP: uniqueMember)"
        }
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
  );
}

function GCPFields({ locale }: { locale: "ko" | "en" }) {
  return (
    <>
      <Form.Item label="GCP project_id" name="gcp_project_id" rules={[{ required: true }]}>
        <Input placeholder="my-project-123" />
      </Form.Item>
      <Form.Item
        label="ENV name for service account key 파일 경로"
        name="gcp_credentials_path_env"
        extra={
          locale === "ko"
            ? "예: GOOGLE_APPLICATION_CREDENTIALS=/secret/sa.json"
            : "e.g. GOOGLE_APPLICATION_CREDENTIALS=/secret/sa.json"
        }
      >
        <Input placeholder="GOOGLE_APPLICATION_CREDENTIALS" />
      </Form.Item>
      <Form.Item
        label={
          locale === "ko"
            ? "또는 ENV name for service account JSON 내용"
            : "Or ENV name for SA JSON content"
        }
        name="gcp_credentials_json_env"
      >
        <Input placeholder="GOOGLE_CREDENTIALS_JSON" />
      </Form.Item>
    </>
  );
}

function AzureFields({ locale }: { locale: "ko" | "en" }) {
  return (
    <>
      <Form.Item label="Azure subscription_id" name="azure_subscription_id" rules={[{ required: true }]}>
        <Input placeholder="00000000-0000-0000-0000-000000000000" />
      </Form.Item>
      <Form.Item
        label={
          locale === "ko"
            ? "scope (선택, 기본 subscription 전체)"
            : "scope (optional, defaults to whole subscription)"
        }
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
  );
}
