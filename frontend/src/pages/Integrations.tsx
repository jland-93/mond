/**
 * 🌙 Integrations — 스캐너/AI 연동 상태
 */

import { useQuery } from "@tanstack/react-query";
import { Card, Col, Row, Tag, Typography } from "antd";

import { api } from "@/lib/api";

const { Title, Paragraph } = Typography;

interface ScannerInfo {
  name: string;
  asset_types: string[];
}

async function fetchScanners(): Promise<{ scanners: ScannerInfo[] }> {
  const { data } = await api.get<{ scanners: ScannerInfo[] }>("/integrations/scanners");
  return data;
}

async function fetchAI(): Promise<{ enabled: boolean; model_default: string; model_deep: string }> {
  const { data } = await api.get("/integrations/ai");
  return data;
}

export default function Integrations() {
  const { data: scanners } = useQuery({ queryKey: ["integrations-scanners"], queryFn: fetchScanners });
  const { data: ai } = useQuery({ queryKey: ["integrations-ai"], queryFn: fetchAI });

  return (
    <div>
      <Title level={2} style={{ marginBottom: 16 }}>
        Integrations
      </Title>

      <Title level={4}>Scanners</Title>
      <Row gutter={[16, 16]}>
        {(scanners?.scanners ?? []).map((s) => (
          <Col xs={24} sm={12} lg={8} key={s.name}>
            <Card title={s.name.toUpperCase()}>
              <Paragraph type="secondary">
                지원 자산 타입:
              </Paragraph>
              {s.asset_types.map((t) => (
                <Tag key={t} color="purple">
                  {t}
                </Tag>
              ))}
            </Card>
          </Col>
        ))}
      </Row>

      <Title level={4} style={{ marginTop: 24 }}>
        AI
      </Title>
      <Card>
        <Paragraph>
          상태:{" "}
          {ai?.enabled ? (
            <Tag color="green">enabled</Tag>
          ) : (
            <Tag color="orange">disabled (heuristic fallback)</Tag>
          )}
        </Paragraph>
        <Paragraph type="secondary">
          기본 모델: <code>{ai?.model_default}</code>
        </Paragraph>
        <Paragraph type="secondary">
          심층 분석 모델: <code>{ai?.model_deep}</code>
        </Paragraph>
      </Card>
    </div>
  );
}
