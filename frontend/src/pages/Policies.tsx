/**
 * Policies — 룰셋 / 컴플라이언스 매핑 (read-only)
 *
 * 정책 수정·삭제·템플릿 적용은 관리자 모드 → '정책 관리'에서만 가능.
 */

import { useQuery } from "@tanstack/react-query";
import { Card, Empty, Input, Segmented, Space, Switch, Table, Tag, Typography } from "antd";
import { useMemo, useState } from "react";

import { useI18n } from "@/i18n";
import { api, type Policy } from "@/lib/api";
import {
  policyTemplatesApi,
  type FrameworkInfo,
} from "@/lib/policy-templates-api";

const { Title, Paragraph } = Typography;

const ALL = "__all__";

async function fetchPolicies(): Promise<Policy[]> {
  const { data } = await api.get<Policy[]>("/policies");
  return data;
}

export default function Policies() {
  const { t, locale } = useI18n();
  const [framework, setFramework] = useState<string>(ALL);
  const [query, setQuery] = useState("");

  const { data, isLoading } = useQuery({ queryKey: ["policies"], queryFn: fetchPolicies });
  const { data: frameworks } = useQuery({
    queryKey: ["policy-templates-frameworks"],
    queryFn: policyTemplatesApi.frameworks,
  });

  const compRefFilter = framework === ALL ? null : framework;

  const filteredPolicies = useMemo(() => {
    const q = query.trim().toLowerCase();
    return (data ?? []).filter((p) => {
      if (compRefFilter && !p.compliance_refs.some((r) => r.startsWith(compRefFilter))) return false;
      if (!q) return true;
      const hay = `${p.name} ${p.description ?? ""} ${p.compliance_refs.join(" ")}`.toLowerCase();
      return hay.includes(q);
    });
  }, [data, compRefFilter, query]);

  return (
    <div>
      <Title level={2} style={{ marginBottom: 8 }}>
        {t.policies.title}
      </Title>
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
      label: f.short_name || (locale === "ko" ? f.name_ko.split(" (")[0] : f.name_en.split(" (")[0]),
      title: locale === "ko" ? f.name_ko : f.name_en,
    })),
  ];
  return (
    <div style={{ overflowX: "auto", paddingBottom: 4 }}>
      <Segmented value={value} onChange={(v) => onChange(v as string)} options={options} />
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
