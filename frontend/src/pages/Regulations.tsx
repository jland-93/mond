/**
 * 🌙 Regulations — 사업 시나리오 → 적용 규제 + 시점 가이드
 */

import { DownloadOutlined } from "@ant-design/icons";
import { useQuery } from "@tanstack/react-query";
import { Button, Card, Empty, Select, Space, Tag, Typography } from "antd";
import { useState } from "react";

import { useI18n } from "@/i18n";
import { api } from "@/lib/api";

const { Title, Paragraph } = Typography;

interface ScenarioLite {
  id: string;
  name: string;
  description: string;
  applicable: string[];
}

interface RegulationFull {
  code: string;
  name: string;
  jurisdiction: string;
  summary: string;
  obligations: string[];
  references: string[];
  timings_detail: Array<{ key: string; label: string }>;
}

interface ScenarioFull {
  id: string;
  name: string;
  description: string;
  applicable: string[];
  regulations: RegulationFull[];
}

const JURIS_COLOR: Record<string, string> = {
  KR: "geekblue",
  EU: "purple",
  US: "magenta",
  GLOBAL: "cyan",
};

export default function Regulations() {
  const { t, locale } = useI18n();
  const [scenarioId, setScenarioId] = useState<string | undefined>(undefined);

  const { data: scenarios } = useQuery({
    queryKey: ["scenarios", locale],
    queryFn: async () => {
      const { data } = await api.get<ScenarioLite[]>("/scenarios", { params: { lang: locale } });
      return data;
    },
  });

  const { data: scenario } = useQuery({
    queryKey: ["scenario", scenarioId, locale],
    queryFn: async () => {
      const { data } = await api.get<ScenarioFull>(`/scenarios/${scenarioId}`, {
        params: { lang: locale },
      });
      return data;
    },
    enabled: !!scenarioId,
  });

  return (
    <div>
      <Title level={2} style={{ marginBottom: 8 }}>
        {t.regulations.title}
      </Title>
      <Paragraph type="secondary">{t.regulations.desc}</Paragraph>

      <Card style={{ marginTop: 12 }}>
        <Space direction="vertical" style={{ width: "100%" }} size="middle">
          <div>
            <strong>{t.regulations.selectScenario}</strong>
          </div>
          <Select
            style={{ width: "100%", maxWidth: 600 }}
            placeholder={t.regulations.selectScenario}
            options={(scenarios ?? []).map((s: ScenarioLite) => ({
              value: s.id,
              label: `${s.name} — ${s.description}`,
            }))}
            value={scenarioId}
            onChange={(v) => setScenarioId(v)}
            showSearch
            optionFilterProp="label"
          />
        </Space>
      </Card>

      {scenarioId && scenario && (
        <div style={{ marginTop: 24 }}>
          <Space style={{ marginBottom: 16 }}>
            <Title level={3} style={{ margin: 0 }}>
              {scenario.name}
            </Title>
            <Button
              icon={<DownloadOutlined />}
              href={`/api/v1/reports/compliance/markdown?scenario=${scenarioId}&lang=${locale}`}
              target="_blank"
              type="primary"
            >
              {t.regulations.downloadMd}
            </Button>
          </Space>
          <Paragraph type="secondary">{scenario.description}</Paragraph>

          <Title level={4} style={{ marginTop: 16 }}>
            {t.regulations.applicable}
          </Title>
          {scenario.regulations.length === 0 && <Empty />}
          <Space direction="vertical" style={{ width: "100%" }} size="middle">
            {scenario.regulations.map((r: RegulationFull) => (
              <Card key={r.code} title={`${r.code} · ${r.name}`}>
                <Space style={{ marginBottom: 12 }}>
                  <Tag color={JURIS_COLOR[r.jurisdiction] ?? "default"}>{r.jurisdiction}</Tag>
                </Space>
                <Paragraph>{r.summary}</Paragraph>

                <strong>{t.regulations.timings}</strong>
                <ul>
                  {r.timings_detail.map((t2: { key: string; label: string }) => (
                    <li key={t2.key}>{t2.label}</li>
                  ))}
                </ul>

                <strong>{t.regulations.obligations}</strong>
                <ul>
                  {r.obligations.map((o: string, i: number) => (
                    <li key={i}>{o}</li>
                  ))}
                </ul>

                {r.references.length > 0 && (
                  <>
                    <strong>{t.regulations.references}</strong>
                    <ul>
                      {r.references.map((ref: string) => (
                        <li key={ref}>
                          <a href={ref} target="_blank" rel="noreferrer">
                            {ref}
                          </a>
                        </li>
                      ))}
                    </ul>
                  </>
                )}
              </Card>
            ))}
          </Space>
        </div>
      )}
    </div>
  );
}
