/**
 * 🌙 Reports — SBOM / Compliance 다운로드
 */

import { DownloadOutlined, ExperimentOutlined } from "@ant-design/icons";
import { useQuery } from "@tanstack/react-query";
import { Alert, Button, Card, Col, Row, Select, Space, Tag, Typography } from "antd";
import { useState } from "react";

import { useI18n } from "@/i18n";
import { api, type Asset, type Page } from "@/lib/api";

const { Title, Paragraph } = Typography;

interface ScenarioLite {
  id: string;
  name: string;
}

export default function Reports() {
  const { t, locale } = useI18n();
  const [assetId, setAssetId] = useState<number | undefined>(undefined);
  const [scenarioId, setScenarioId] = useState<string | undefined>(undefined);

  const { data: assets } = useQuery({
    queryKey: ["assets-lite-reports"],
    queryFn: async () => {
      const { data } = await api.get<Page<Asset>>("/assets", { params: { limit: 200 } });
      return data.items;
    },
  });

  const { data: scenarios } = useQuery({
    queryKey: ["scenarios-lite", locale],
    queryFn: async () => {
      const { data } = await api.get<ScenarioLite[]>("/scenarios", { params: { lang: locale } });
      return data;
    },
  });

  return (
    <div>
      <Title level={2} style={{ marginBottom: 16 }}>
        {t.reports.title}
      </Title>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <span>{t.reports.sbom}</span>
                <Tag color="orange" icon={<ExperimentOutlined />}>
                  experimental
                </Tag>
              </Space>
            }
          >
            <Alert
              type="warning"
              showIcon
              style={{ marginBottom: 12 }}
              message={
                locale === "ko"
                  ? "SBOM은 현재 CycloneDX-lite stub입니다. 실제 의존성 추출 (package.json·go.mod·Dockerfile 파싱)은 v0.2 로드맵."
                  : "SBOM is a CycloneDX-lite stub. Real dependency extraction (package.json · go.mod · Dockerfile) is on the v0.2 roadmap."
              }
            />
            <Paragraph type="secondary">{t.reports.sbomDesc}</Paragraph>
            <Space direction="vertical" style={{ width: "100%" }}>
              <Select
                style={{ width: "100%" }}
                placeholder={t.reports.pickAsset}
                value={assetId}
                onChange={setAssetId}
                showSearch
                optionFilterProp="label"
                options={(assets ?? []).map((a: Asset) => ({
                  value: a.id,
                  label: `${a.name} (${a.asset_type})`,
                }))}
              />
              <Button
                type="primary"
                icon={<DownloadOutlined />}
                disabled={!assetId}
                href={assetId ? `/api/v1/reports/sbom?asset_id=${assetId}` : undefined}
                target="_blank"
                block
              >
                {t.reports.downloadJson}
              </Button>
            </Space>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title={t.reports.compliance}>
            <Paragraph type="secondary">{t.reports.complianceDesc}</Paragraph>
            <Space direction="vertical" style={{ width: "100%" }}>
              <Select
                style={{ width: "100%" }}
                placeholder={t.reports.pickScenario}
                value={scenarioId}
                onChange={setScenarioId}
                showSearch
                optionFilterProp="label"
                options={(scenarios ?? []).map((s: ScenarioLite) => ({ value: s.id, label: s.name }))}
              />
              <Space style={{ width: "100%" }}>
                <Button
                  type="primary"
                  icon={<DownloadOutlined />}
                  disabled={!scenarioId}
                  href={
                    scenarioId
                      ? `/api/v1/reports/compliance/markdown?scenario=${scenarioId}&lang=${locale}`
                      : undefined
                  }
                  target="_blank"
                >
                  {t.reports.downloadMarkdown}
                </Button>
                <Button
                  icon={<DownloadOutlined />}
                  disabled={!scenarioId}
                  href={
                    scenarioId
                      ? `/api/v1/reports/compliance?scenario=${scenarioId}&lang=${locale}`
                      : undefined
                  }
                  target="_blank"
                >
                  {t.reports.downloadJson}
                </Button>
              </Space>
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  );
}
