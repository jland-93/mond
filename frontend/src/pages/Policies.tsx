/**
 * 🌙 Policies — 룰셋 / 컴플라이언스 매핑 + 한국·글로벌 규제 템플릿 카탈로그
 */

import { AppstoreAddOutlined, SafetyOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  Button,
  Card,
  Checkbox,
  Empty,
  Input,
  Modal,
  Segmented,
  Space,
  Switch,
  Table,
  Tag,
  Tooltip,
  Typography,
  message,
} from "antd";
import { useAuth } from "@/auth/AuthContext";
import { useMemo, useState } from "react";

import { useI18n } from "@/i18n";
import { api, type Policy } from "@/lib/api";
import { hasRole } from "@/lib/auth-api";
import {
  policyTemplatesApi,
  type FrameworkInfo,
  type PolicyTemplate,
} from "@/lib/policy-templates-api";

const { Title, Paragraph, Text } = Typography;

const ALL = "__all__";

async function fetchPolicies(): Promise<Policy[]> {
  const { data } = await api.get<Policy[]>("/policies");
  return data;
}

export default function Policies() {
  const { t, locale } = useI18n();
  const { user } = useAuth();
  const qc = useQueryClient();
  const [catalogOpen, setCatalogOpen] = useState(false);
  const [framework, setFramework] = useState<string>(ALL);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const { data, isLoading } = useQuery({ queryKey: ["policies"], queryFn: fetchPolicies });
  const { data: frameworks } = useQuery({
    queryKey: ["policy-templates-frameworks"],
    queryFn: policyTemplatesApi.frameworks,
  });
  const { data: templates } = useQuery({
    queryKey: ["policy-templates"],
    queryFn: () => policyTemplatesApi.list(),
    enabled: catalogOpen,
  });

  const installed = useMemo(
    () => new Set((data ?? []).map((p) => p.name)),
    [data],
  );
  const compRefFilter = framework === ALL ? null : framework;

  // 적용된 정책 — 컴플라이언스 ref / 텍스트로 필터
  const filteredPolicies = useMemo(() => {
    const q = query.trim().toLowerCase();
    return (data ?? []).filter((p) => {
      if (compRefFilter && !p.compliance_refs.some((r) => r.startsWith(compRefFilter))) return false;
      if (!q) return true;
      const hay = `${p.name} ${p.description ?? ""} ${p.compliance_refs.join(" ")}`.toLowerCase();
      return hay.includes(q);
    });
  }, [data, compRefFilter, query]);

  // 템플릿 카탈로그 — 같은 framework로 필터 + 검색
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
          ? `${res.installed}건 적용됨 · 기존 중복 ${res.skipped_existing}건 건너뜀`
          : `Installed ${res.installed} · skipped ${res.skipped_existing}`,
      );
      qc.invalidateQueries({ queryKey: ["policies"] });
      setSelected(new Set());
      setCatalogOpen(false);
    },
    onError: (err: Error & { response?: { data?: { detail?: string } } }) =>
      message.error(err.response?.data?.detail ?? err.message),
  });

  const canInstall = hasRole(user, "admin");

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
        <Title level={2} style={{ margin: 0 }}>
          {t.policies.title}
        </Title>
        <Tooltip title={canInstall ? "" : (locale === "ko" ? "ADMIN 권한 필요" : "ADMIN required")}>
          <Button
            type="primary"
            icon={<AppstoreAddOutlined />}
            disabled={!canInstall}
            onClick={() => setCatalogOpen(true)}
          >
            {t.policies.openCatalog}
          </Button>
        </Tooltip>
      </div>
      <Paragraph type="secondary">{t.policies.desc}</Paragraph>

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
            { title: t.policies.threshold, dataIndex: "severity_threshold", width: 120 },
            {
              title: t.common.enabled,
              dataIndex: "enabled",
              render: (v: boolean) => <Switch checked={v} disabled />,
              width: 100,
            },
            {
              title: t.policies.compliance,
              dataIndex: "compliance_refs",
              render: (refs: string[]) => (
                <Space size={[4, 4]} wrap>
                  {(refs ?? []).map((r) => (
                    <Tag key={r} color={tagColor(r)}>
                      {r}
                    </Tag>
                  ))}
                </Space>
              ),
            },
            { title: t.common.description, dataIndex: "description", ellipsis: true },
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
                        <Paragraph style={{ marginTop: 6, marginBottom: 6 }}>
                          {tpl.description}
                        </Paragraph>
                        <Space size={[4, 4]} wrap>
                          {tpl.compliance_refs.map((r) => (
                            <Tag key={r} color={tagColor(r)}>
                              {r}
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
    </div>
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
      label: locale === "ko" ? f.name_ko.split(" (")[0] : f.name_en.split(" (")[0],
    })),
  ];
  return (
    <Segmented
      block
      value={value}
      onChange={(v) => onChange(v as string)}
      options={options}
    />
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
