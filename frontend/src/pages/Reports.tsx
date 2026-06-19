/**
 * Reports — SBOM / Compliance 다운로드
 */

import { DownloadOutlined, ExperimentOutlined, FileSearchOutlined } from "@ant-design/icons";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Alert, Button, Card, Col, Input, Row, Select, Space, Table, Tag, Typography, message } from "antd";
import { useState } from "react";

import { useI18n } from "@/i18n";
import { api, type Asset, type Page } from "@/lib/api";

const { Title, Paragraph, Text } = Typography;

interface ParsedPackage {
  name: string;
  version: string | null;
  ecosystem: string;
  dev: boolean;
}

interface ParseResult {
  filename: string;
  ecosystem: string;
  count: number;
  packages: ParsedPackage[];
}

interface ScenarioLite {
  id: string;
  name: string;
}

export default function Reports() {
  const { t, locale } = useI18n();
  const [assetId, setAssetId] = useState<number | undefined>(undefined);
  const [scenarioId, setScenarioId] = useState<string | undefined>(undefined);

  // SBOM 파일 파싱 (실 추출)
  const [filename, setFilename] = useState("package.json");
  const [content, setContent] = useState("");
  const [parsed, setParsed] = useState<ParseResult | null>(null);

  const parseSbom = useMutation({
    mutationFn: async () => {
      const { data } = await api.post<ParseResult>("/reports/sbom/parse", { filename, content });
      return data;
    },
    onSuccess: (r) => {
      setParsed(r);
      message.success(
        locale === "ko"
          ? `${r.count}개 패키지 추출 (${r.ecosystem})`
          : `${r.count} packages extracted (${r.ecosystem})`,
      );
    },
    onError: (e: Error & { response?: { data?: { detail?: string } } }) =>
      message.error(e.response?.data?.detail ?? e.message),
  });

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
              type="info"
              showIcon
              style={{ marginBottom: 12 }}
              message={
                locale === "ko"
                  ? "이 카드의 SBOM은 자산의 finding을 묶은 CycloneDX-lite입니다. 의존성 파일 직접 파싱은 아래 'SBOM 파일 파싱' 카드 사용."
                  : "This SBOM is a finding-based CycloneDX-lite. For real dependency parsing use the 'SBOM File Parsing' card below."
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

        <Col xs={24}>
          <Card
            title={
              <Space>
                <FileSearchOutlined />
                <span>{locale === "ko" ? "SBOM 파일 파싱" : "SBOM File Parsing"}</span>
                <Tag color="blue">npm · pypi · go · docker</Tag>
              </Space>
            }
          >
            <Paragraph type="secondary">
              {locale === "ko"
                ? "package.json / package-lock.json / requirements.txt / go.mod / Dockerfile 내용을 붙여 넣으면 의존성을 추출합니다."
                : "Paste contents of package.json / package-lock.json / requirements.txt / go.mod / Dockerfile to extract dependencies."}
            </Paragraph>
            <Space style={{ width: "100%", marginBottom: 12 }} wrap>
              <Select
                style={{ width: 240 }}
                value={filename}
                onChange={setFilename}
                options={[
                  { value: "package.json", label: "package.json" },
                  { value: "package-lock.json", label: "package-lock.json" },
                  { value: "requirements.txt", label: "requirements.txt" },
                  { value: "go.mod", label: "go.mod" },
                  { value: "Dockerfile", label: "Dockerfile" },
                ]}
              />
              <Button
                type="primary"
                onClick={() => parseSbom.mutate()}
                disabled={!content.trim()}
                loading={parseSbom.isPending}
              >
                {locale === "ko" ? "추출" : "Parse"}
              </Button>
              {parsed && (
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {locale === "ko"
                    ? `${parsed.ecosystem} · ${parsed.count}개`
                    : `${parsed.ecosystem} · ${parsed.count} packages`}
                </Text>
              )}
            </Space>
            <Input.TextArea
              rows={6}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder={locale === "ko" ? "파일 내용 붙여넣기" : "Paste file content"}
              style={{ fontFamily: "monospace", fontSize: 12, marginBottom: 12 }}
            />

            {parsed && parsed.packages.length > 0 && (
              <Table
                size="small"
                rowKey={(r: ParsedPackage, i?: number) => `${r.name}@${r.version}@${i}`}
                dataSource={parsed.packages}
                pagination={{ pageSize: 20 }}
                columns={[
                  { title: locale === "ko" ? "패키지" : "Name", dataIndex: "name" },
                  { title: locale === "ko" ? "버전" : "Version", dataIndex: "version", width: 180, render: (v: string | null) => v ?? "—" },
                  {
                    title: "ecosystem",
                    dataIndex: "ecosystem",
                    width: 110,
                    render: (e: string) => <Tag>{e}</Tag>,
                  },
                  {
                    title: locale === "ko" ? "dev" : "dev",
                    dataIndex: "dev",
                    width: 70,
                    render: (d: boolean) => (d ? <Tag>dev</Tag> : null),
                  },
                ]}
              />
            )}
          </Card>
        </Col>
      </Row>
    </div>
  );
}
