/**
 * Admin · Policy Management — 정책 enable/disable, threshold 조정, 삭제 + 템플릿 카탈로그
 */

import { AppstoreAddOutlined, DeleteOutlined, PlusOutlined, SafetyOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  Button,
  Card,
  Checkbox,
  Empty,
  Form,
  Input,
  Modal,
  Popconfirm,
  Segmented,
  Select,
  Space,
  Switch,
  Table,
  Tag,
  Typography,
  message,
} from "antd";
import { useMemo, useState } from "react";

import { useI18n } from "@/i18n";
import { api, type Policy } from "@/lib/api";
import {
  policyTemplatesApi,
  type FrameworkInfo,
  type PolicyTemplate,
} from "@/lib/policy-templates-api";

const { Title, Paragraph, Text } = Typography;

const ALL = "__all__";
const SEVERITIES = ["critical", "high", "medium", "low", "info"];

const SEVERITY_COLOR: Record<string, string> = {
  critical: "#e8484a",
  high: "#f29142",
  medium: "#eab308",
  low: "#4ad28d",
  info: "#8a8aff",
};

const ENGINE_COLOR: Record<string, string> = {
  builtin: "default",
  opa: "geekblue",
};

async function fetchPolicies(): Promise<Policy[]> {
  const { data } = await api.get<Policy[]>("/policies");
  return data;
}

export default function AdminPolicies() {
  const { t, locale } = useI18n();
  const qc = useQueryClient();
  const [catalogOpen, setCatalogOpen] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [framework, setFramework] = useState<string>(ALL);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const { data: policies, isLoading } = useQuery({ queryKey: ["policies"], queryFn: fetchPolicies });
  const { data: frameworks } = useQuery({
    queryKey: ["policy-templates-frameworks"],
    queryFn: policyTemplatesApi.frameworks,
  });
  const { data: templates } = useQuery({
    queryKey: ["policy-templates"],
    queryFn: () => policyTemplatesApi.list(),
    enabled: catalogOpen,
  });

  const updatePolicy = useMutation({
    mutationFn: ({ id, patch }: { id: number; patch: Partial<Policy> }) =>
      api.patch<Policy>(`/policies/${id}`, patch).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["policies"] }),
  });

  const deletePolicy = useMutation({
    mutationFn: (id: number) => api.delete(`/policies/${id}`),
    onSuccess: () => {
      message.success(locale === "ko" ? "삭제됨" : "Deleted");
      qc.invalidateQueries({ queryKey: ["policies"] });
    },
  });

  const installed = useMemo(() => new Set((policies ?? []).map((p) => p.name)), [policies]);
  const compRefFilter = framework === ALL ? null : framework;

  const filteredPolicies = useMemo(() => {
    const q = query.trim().toLowerCase();
    return (policies ?? []).filter((p) => {
      if (compRefFilter && !p.compliance_refs.some((r) => r.startsWith(compRefFilter))) return false;
      if (!q) return true;
      const hay = `${p.name} ${p.description ?? ""} ${p.compliance_refs.join(" ")}`.toLowerCase();
      return hay.includes(q);
    });
  }, [policies, compRefFilter, query]);

  const filteredTemplates = useMemo(() => {
    const q = query.trim().toLowerCase();
    return (templates ?? []).filter((tpl) => {
      if (compRefFilter && !tpl.frameworks.includes(compRefFilter)) return false;
      if (!q) return true;
      return (
        tpl.name.toLowerCase().includes(q) ||
        tpl.description.toLowerCase().includes(q) ||
        tpl.compliance_refs.some((r) => r.toLowerCase().includes(q))
      );
    });
  }, [templates, compRefFilter, query]);

  const install = useMutation({
    mutationFn: (names: string[]) => policyTemplatesApi.install(names),
    onSuccess: (res) => {
      message.success(
        locale === "ko"
          ? `${res.installed}건 적용 · 중복 ${res.skipped_existing}건`
          : `Installed ${res.installed} · skipped ${res.skipped_existing}`,
      );
      qc.invalidateQueries({ queryKey: ["policies"] });
      setSelected(new Set());
      setCatalogOpen(false);
    },
  });

  const createCustom = useMutation({
    mutationFn: (payload: Partial<Policy>) =>
      api.post<Policy>("/policies", payload).then((r) => r.data),
    onSuccess: (p) => {
      message.success(locale === "ko" ? `'${p.name}' 추가됨` : `Created '${p.name}'`);
      qc.invalidateQueries({ queryKey: ["policies"] });
      setCreateOpen(false);
    },
    onError: (e: Error & { response?: { data?: { detail?: string } } }) => {
      message.error(e.response?.data?.detail ?? e.message);
    },
  });

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
        <Title level={2} style={{ margin: 0 }}>
          {t.adminArea.policyMgmtTitle}
        </Title>
        <Space>
          <Button icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
            {t.policies.createCustom}
          </Button>
          <Button type="primary" icon={<AppstoreAddOutlined />} onClick={() => setCatalogOpen(true)}>
            {t.policies.openCatalog}
          </Button>
        </Space>
      </div>
      <Paragraph type="secondary">{t.adminArea.policyMgmtDesc}</Paragraph>

      <Card style={{ marginBottom: 16 }}>
        <Space direction="vertical" style={{ width: "100%" }}>
          <FrameworkFilter
            value={framework}
            onChange={setFramework}
            frameworks={frameworks ?? []}
            locale={locale}
            t={t}
          />
          <Input.Search
            placeholder={t.policies.searchPlaceholder}
            allowClear
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </Space>
      </Card>

      <Card>
        <Table
          loading={isLoading}
          dataSource={filteredPolicies}
          rowKey="id"
          locale={{
            emptyText: <Empty description={locale === "ko" ? "정책이 없습니다" : "No policies"} />,
          }}
          columns={[
            { title: t.common.name, dataIndex: "name" },
            {
              title: t.common.type,
              dataIndex: "policy_type",
              render: (v: string) => <Tag color="purple">{v}</Tag>,
              width: 130,
            },
            {
              title: t.policies.threshold,
              dataIndex: "severity_threshold",
              width: 130,
              render: (v: string, r: Policy) => (
                <Select
                  size="small"
                  value={v}
                  style={{ width: "100%" }}
                  options={SEVERITIES.map((s) => ({
                    value: s,
                    label: (
                      <Space size={6}>
                        <span
                          style={{
                            display: "inline-block",
                            width: 8,
                            height: 8,
                            borderRadius: "50%",
                            background: SEVERITY_COLOR[s],
                          }}
                        />
                        <span>{s}</span>
                      </Space>
                    ),
                  }))}
                  onChange={(val) =>
                    updatePolicy.mutate({ id: r.id, patch: { severity_threshold: val } as Partial<Policy> })
                  }
                />
              ),
            },
            {
              title: "engine",
              dataIndex: "engine",
              width: 100,
              render: (v: string) => (
                <Tag color={ENGINE_COLOR[v] ?? "default"}>{v || "builtin"}</Tag>
              ),
            },
            {
              title: t.common.enabled,
              dataIndex: "enabled",
              render: (v: boolean, r: Policy) => (
                <Switch
                  checked={v}
                  onChange={(checked) =>
                    updatePolicy.mutate({ id: r.id, patch: { enabled: checked } as Partial<Policy> })
                  }
                />
              ),
              width: 100,
            },
            {
              title: t.policies.compliance,
              dataIndex: "compliance_refs",
              render: (refs: string[]) => (
                <Space size={[4, 4]} wrap>
                  {(refs ?? []).map((rf) => (
                    <Tag key={rf} color={tagColor(rf)}>
                      {rf}
                    </Tag>
                  ))}
                </Space>
              ),
            },
            { title: t.common.description, dataIndex: "description", ellipsis: true },
            {
              title: "",
              width: 60,
              render: (_: unknown, r: Policy) => (
                <Popconfirm
                  title={locale === "ko" ? "이 정책을 삭제할까요?" : "Delete this policy?"}
                  okType="danger"
                  onConfirm={() => deletePolicy.mutate(r.id)}
                >
                  <Button size="small" type="text" danger icon={<DeleteOutlined />} />
                </Popconfirm>
              ),
            },
          ]}
        />
      </Card>

      <Modal
        title={
          <Space>
            <SafetyOutlined />
            <span>{t.policies.catalogTitle}</span>
          </Space>
        }
        open={catalogOpen}
        onCancel={() => {
          setCatalogOpen(false);
          setSelected(new Set());
        }}
        width={920}
        okText={`${t.policies.installSelected} (${selected.size})`}
        okButtonProps={{ disabled: selected.size === 0 || install.isPending }}
        confirmLoading={install.isPending}
        onOk={() => install.mutate(Array.from(selected))}
      >
        <Paragraph type="secondary">{t.policies.catalogDesc}</Paragraph>
        <Space direction="vertical" style={{ width: "100%" }} size="middle">
          <FrameworkFilter
            value={framework}
            onChange={setFramework}
            frameworks={frameworks ?? []}
            locale={locale}
            t={t}
          />
          <Input.Search
            placeholder={t.policies.searchPlaceholder}
            allowClear
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <Alert
            type="info"
            showIcon
            message={
              locale === "ko"
                ? `${filteredTemplates.length}개 템플릿 · 이미 적용된 정책은 자동으로 건너뜁니다.`
                : `${filteredTemplates.length} templates · already-installed ones are skipped.`
            }
          />
          <div style={{ maxHeight: 460, overflowY: "auto", paddingRight: 4 }}>
            <Space direction="vertical" style={{ width: "100%" }}>
              {filteredTemplates.map((tpl: PolicyTemplate) => {
                const isInstalled = installed.has(tpl.name);
                const isChecked = selected.has(tpl.name);
                return (
                  <Card
                    key={tpl.name}
                    size="small"
                    style={{
                      borderColor: isChecked ? "var(--mond-primary)" : undefined,
                      opacity: isInstalled ? 0.55 : 1,
                    }}
                  >
                    <Space align="start" style={{ width: "100%" }}>
                      <Checkbox
                        checked={isChecked}
                        disabled={isInstalled}
                        onChange={(e) => {
                          setSelected((cur) => {
                            const n = new Set(cur);
                            if (e.target.checked) n.add(tpl.name);
                            else n.delete(tpl.name);
                            return n;
                          });
                        }}
                      />
                      <div style={{ flex: 1 }}>
                        <Space size={[6, 6]} wrap>
                          <Text strong>{tpl.name}</Text>
                          <Tag color="purple">{tpl.policy_type}</Tag>
                          <Tag>{tpl.severity_threshold}</Tag>
                          {isInstalled && (
                            <Tag color="default">
                              {locale === "ko" ? "이미 적용됨" : "Installed"}
                            </Tag>
                          )}
                        </Space>
                        <Paragraph style={{ marginTop: 6, marginBottom: 6 }}>{tpl.description}</Paragraph>
                        <Space size={[4, 4]} wrap>
                          {tpl.compliance_refs.map((rf) => (
                            <Tag key={rf} color={tagColor(rf)}>
                              {rf}
                            </Tag>
                          ))}
                        </Space>
                      </div>
                    </Space>
                  </Card>
                );
              })}
              {filteredTemplates.length === 0 && (
                <Empty description={locale === "ko" ? "해당 규제 템플릿이 없습니다" : "No templates"} />
              )}
            </Space>
          </div>
        </Space>
      </Modal>

      <CustomPolicyModal
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        onSubmit={(values) => createCustom.mutate(values)}
        submitting={createCustom.isPending}
        locale={locale}
        t={t}
      />
    </div>
  );
}

function CustomPolicyModal({
  open,
  onCancel,
  onSubmit,
  submitting,
  locale,
  t,
}: {
  open: boolean;
  onCancel: () => void;
  onSubmit: (values: Partial<Policy>) => void;
  submitting: boolean;
  locale: "ko" | "en";
  t: {
    policies: {
      createCustomTitle: string;
      createCustomDesc: string;
      fieldName: string;
      fieldType: string;
      fieldThreshold: string;
      fieldDescription: string;
      fieldComplianceRefs: string;
      fieldComplianceRefsHint: string;
      fieldDefinition: string;
      fieldDefinitionHint: string;
      invalidJson: string;
      create: string;
    };
  };
}) {
  const [form] = Form.useForm();
  const TYPES = ["sast", "sca", "iac", "dast", "container", "secrets", "compliance", "custom"];
  return (
    <Modal
      title={
        <Space>
          <PlusOutlined />
          <span>{t.policies.createCustomTitle}</span>
        </Space>
      }
      open={open}
      onCancel={() => {
        form.resetFields();
        onCancel();
      }}
      width={720}
      okText={t.policies.create}
      confirmLoading={submitting}
      onOk={() => form.submit()}
    >
      <Paragraph type="secondary">{t.policies.createCustomDesc}</Paragraph>
      <Form
        form={form}
        layout="vertical"
        initialValues={{
          policy_type: "custom",
          severity_threshold: "high",
          enabled: true,
        }}
        onFinish={(values: {
          name: string;
          policy_type: string;
          description?: string;
          severity_threshold: string;
          compliance_refs?: string[];
          definition_json?: string;
        }) => {
          let definition: Record<string, unknown> = {};
          if (values.definition_json?.trim()) {
            try {
              definition = JSON.parse(values.definition_json);
            } catch {
              message.error(t.policies.invalidJson);
              return;
            }
          }
          onSubmit({
            name: values.name.trim(),
            policy_type: values.policy_type as Policy["policy_type"],
            description: values.description?.trim() || undefined,
            severity_threshold: values.severity_threshold,
            compliance_refs: values.compliance_refs ?? [],
            definition,
            enabled: true,
          } as Partial<Policy>);
          form.resetFields();
        }}
      >
        <Form.Item
          label={t.policies.fieldName}
          name="name"
          rules={[{ required: true, min: 3, max: 120 }]}
        >
          <Input placeholder={locale === "ko" ? "예: 사내 — 망분리 강제" : "e.g. Internal — Enforce network segregation"} />
        </Form.Item>

        <Space style={{ width: "100%" }} size="middle">
          <Form.Item label={t.policies.fieldType} name="policy_type" style={{ width: 200 }}>
            <Select options={TYPES.map((v) => ({ value: v, label: v }))} />
          </Form.Item>
          <Form.Item label={t.policies.fieldThreshold} name="severity_threshold" style={{ width: 200 }}>
            <Select
              options={SEVERITIES.map((s) => ({
                value: s,
                label: (
                  <Space size={6}>
                    <span
                      style={{
                        display: "inline-block",
                        width: 8,
                        height: 8,
                        borderRadius: "50%",
                        background: SEVERITY_COLOR[s],
                      }}
                    />
                    <span>{s}</span>
                  </Space>
                ),
              }))}
            />
          </Form.Item>
        </Space>

        <Form.Item label={t.policies.fieldDescription} name="description">
          <Input.TextArea
            rows={2}
            placeholder={locale === "ko" ? "이 통제의 목적과 적용 범위" : "Purpose and scope of this control"}
          />
        </Form.Item>

        <Form.Item
          label={t.policies.fieldComplianceRefs}
          name="compliance_refs"
          extra={t.policies.fieldComplianceRefsHint}
        >
          <Select
            mode="tags"
            tokenSeparators={[",", " "]}
            placeholder="INTERNAL-SEC-01"
          />
        </Form.Item>

        <Form.Item
          label={t.policies.fieldDefinition}
          name="definition_json"
          extra={t.policies.fieldDefinitionHint}
        >
          <Input.TextArea rows={4} placeholder='{"min_tls_version":"1.2"}' style={{ fontFamily: "monospace" }} />
        </Form.Item>
      </Form>
    </Modal>
  );
}

function FrameworkFilter({
  value,
  onChange,
  frameworks,
  locale,
  t,
}: {
  value: string;
  onChange: (v: string) => void;
  frameworks: FrameworkInfo[];
  locale: "ko" | "en";
  t: { policies: { allFrameworks: string } };
}) {
  const options = [
    { value: ALL, label: t.policies.allFrameworks },
    ...frameworks.map((f) => ({
      value: f.id,
      label: f.short_name || (locale === "ko" ? f.name_ko.split(" (")[0] : f.name_en.split(" (")[0]),
      title: locale === "ko" ? f.name_ko : f.name_en,
    })),
  ];
  return (
    <div style={{ overflowX: "auto", paddingBottom: 4 }}>
      <Segmented
        value={value}
        onChange={(v) => onChange(v as string)}
        options={options}
      />
    </div>
  );
}

function tagColor(ref: string): string {
  if (ref.startsWith("ISMS-P")) return "geekblue";
  if (ref.startsWith("K-EFSA")) return "blue";
  if (ref.startsWith("K-CSAP")) return "cyan";
  if (ref.startsWith("K-PIPA")) return "volcano";
  if (ref.startsWith("ISO-27001")) return "purple";
  if (ref.startsWith("OWASP")) return "magenta";
  if (ref.startsWith("CIS")) return "gold";
  if (ref.startsWith("PCI")) return "red";
  if (ref.startsWith("GDPR")) return "lime";
  return "default";
}
