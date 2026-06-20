/**
 * Regulations — 사업 시나리오 → 적용 규제 + 시점 가이드
 *
 * 미선택 상태에선 시나리오 카드 그리드로 직접 탐색.
 * 선택 후엔 시나리오 헤더 + 규제 카드들(관할별 색 강조 + 시점/의무 시각화).
 */

import {
  ArrowLeftOutlined,
  ClockCircleOutlined,
  DownloadOutlined,
  FileTextOutlined,
  LinkOutlined,
} from "@ant-design/icons";
import { useQuery } from "@tanstack/react-query";
import { Button, Card, Col, Empty, Row, Select, Space, Tag, Typography } from "antd";
import { useState } from "react";

import { useI18n } from "@/i18n";
import { api } from "@/lib/api";

const { Title, Paragraph, Text } = Typography;

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

const JURIS_LABEL: Record<string, { ko: string; en: string }> = {
  KR: { ko: "한국", en: "Korea" },
  EU: { ko: "유럽", en: "EU" },
  US: { ko: "미국", en: "US" },
  GLOBAL: { ko: "글로벌", en: "Global" },
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

      {/* 시나리오 선택기 — 항상 노출 */}
      <Card style={{ marginTop: 12 }}>
        <Space direction="vertical" style={{ width: "100%" }} size="small">
          <Text strong>{t.regulations.selectScenario}</Text>
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
            allowClear
          />
        </Space>
      </Card>

      {/* 미선택 시 시나리오 카드 그리드 */}
      {!scenarioId && (
        <div style={{ marginTop: 24 }}>
          <Title level={4} style={{ marginBottom: 12 }}>
            {locale === "ko" ? "어떤 사업이신가요?" : "What's your scenario?"}
          </Title>
          <Paragraph type="secondary" style={{ marginBottom: 16 }}>
            {locale === "ko"
              ? "카드를 클릭하면 적용되는 규제·시점·의무를 모두 보여드립니다."
              : "Click a card to see all applicable regulations, timings, and obligations."}
          </Paragraph>
          <Row gutter={[16, 16]}>
            {(scenarios ?? []).map((s) => (
              <Col xs={24} md={12} xl={8} key={s.id}>
                <Card
                  hoverable
                  onClick={() => setScenarioId(s.id)}
                  style={{ height: "100%", cursor: "pointer" }}
                >
                  <Text strong style={{ display: "block", fontSize: 15, marginBottom: 6 }}>
                    {s.name}
                  </Text>
                  <Paragraph type="secondary" style={{ marginBottom: 12 }}>
                    {s.description}
                  </Paragraph>
                  <Space size={[4, 4]} wrap>
                    {s.applicable.slice(0, 5).map((code) => (
                      <Tag key={code} style={{ marginInlineEnd: 0 }}>
                        {code}
                      </Tag>
                    ))}
                    {s.applicable.length > 5 && (
                      <Tag style={{ marginInlineEnd: 0 }}>+{s.applicable.length - 5}</Tag>
                    )}
                  </Space>
                </Card>
              </Col>
            ))}
          </Row>
        </div>
      )}

      {/* 선택된 시나리오 상세 */}
      {scenarioId && scenario && (
        <div style={{ marginTop: 24 }}>
          {/* 헤더 + 다운로드 + 뒤로 */}
          <Card style={{ marginBottom: 16 }} styles={{ body: { paddingBlock: 16 } }}>
            <Space style={{ width: "100%", justifyContent: "space-between" }} align="start">
              <Space direction="vertical" size={4}>
                <Space size={6}>
                  <Button
                    size="small"
                    type="text"
                    icon={<ArrowLeftOutlined />}
                    onClick={() => setScenarioId(undefined)}
                  >
                    {locale === "ko" ? "다른 시나리오" : "Switch"}
                  </Button>
                </Space>
                <Title level={3} style={{ margin: 0 }}>
                  {scenario.name}
                </Title>
                <Text type="secondary">{scenario.description}</Text>
                <Space size={[4, 4]} wrap style={{ marginTop: 4 }}>
                  <Tag color="cyan" style={{ marginInlineEnd: 0 }}>
                    {locale === "ko" ? "적용 규제" : "Applicable"} {scenario.regulations.length}
                  </Tag>
                </Space>
              </Space>
              <Button
                icon={<DownloadOutlined />}
                href={`/api/v1/reports/compliance/markdown?scenario=${scenarioId}&lang=${locale}`}
                target="_blank"
                type="primary"
              >
                {t.regulations.downloadMd}
              </Button>
            </Space>
          </Card>

          {scenario.regulations.length === 0 && (
            <Empty
              description={
                locale === "ko" ? "이 시나리오에 매핑된 규제가 없습니다." : "No regulations mapped."
              }
            />
          )}

          <Row gutter={[16, 16]}>
            {scenario.regulations.map((r: RegulationFull) => {
              const jurisColor = JURIS_COLOR[r.jurisdiction] ?? "default";
              const jurisLabel = JURIS_LABEL[r.jurisdiction]?.[locale] ?? r.jurisdiction;
              return (
                <Col xs={24} xl={12} key={r.code}>
                  <Card
                    style={{ height: "100%" }}
                    title={
                      <Space size={6} wrap>
                        <Tag color={jurisColor} style={{ marginInlineEnd: 0 }}>
                          {jurisLabel} · {r.jurisdiction}
                        </Tag>
                        <Text strong>{r.code}</Text>
                        <Text type="secondary" style={{ fontWeight: 400 }}>
                          {r.name}
                        </Text>
                      </Space>
                    }
                  >
                    <Paragraph style={{ marginBottom: 12 }}>{r.summary}</Paragraph>

                    {r.timings_detail.length > 0 && (
                      <div style={{ marginBottom: 12 }}>
                        <Space size={4} style={{ marginBottom: 6 }}>
                          <ClockCircleOutlined style={{ color: "var(--mond-text-dim)" }} />
                          <Text strong>{t.regulations.timings}</Text>
                        </Space>
                        <Space size={[4, 4]} wrap>
                          {r.timings_detail.map((t2) => (
                            <Tag key={t2.key} color="default" style={{ marginInlineEnd: 0 }}>
                              {t2.label}
                            </Tag>
                          ))}
                        </Space>
                      </div>
                    )}

                    {r.obligations.length > 0 && (
                      <div style={{ marginBottom: 12 }}>
                        <Space size={4} style={{ marginBottom: 6 }}>
                          <FileTextOutlined style={{ color: "var(--mond-text-dim)" }} />
                          <Text strong>{t.regulations.obligations}</Text>
                        </Space>
                        <ul style={{ marginBottom: 0, paddingInlineStart: 18 }}>
                          {r.obligations.map((o: string, i: number) => (
                            <li key={i} style={{ marginBottom: 4 }}>
                              {o}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {r.references.length > 0 && (
                      <div>
                        <Space size={4} style={{ marginBottom: 6 }}>
                          <LinkOutlined style={{ color: "var(--mond-text-dim)" }} />
                          <Text strong>{t.regulations.references}</Text>
                        </Space>
                        <ul style={{ marginBottom: 0, paddingInlineStart: 18 }}>
                          {r.references.map((ref: string) => (
                            <li key={ref}>
                              <a href={ref} target="_blank" rel="noreferrer">
                                {ref}
                              </a>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </Card>
                </Col>
              );
            })}
          </Row>
        </div>
      )}
    </div>
  );
}
