/**
 * Integrations — Scanners / AI / MCP / Webhooks / Notifications
 */

import { useQuery } from "@tanstack/react-query";
import { Alert, Card, Col, Row, Tag, Typography } from "antd";

import { useI18n } from "@/i18n";
import { api } from "@/lib/api";

const { Title, Paragraph, Text } = Typography;

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
  const { t } = useI18n();
  const { data: scanners } = useQuery({ queryKey: ["integrations-scanners"], queryFn: fetchScanners });
  const { data: ai } = useQuery({ queryKey: ["integrations-ai"], queryFn: fetchAI });

  return (
    <div>
      <Title level={2} style={{ marginBottom: 16 }}>
        {t.integrations.title}
      </Title>

      <Title level={4}>{t.integrations.scanners}</Title>
      <Row gutter={[16, 16]}>
        {(scanners?.scanners ?? []).map((s) => (
          <Col xs={24} sm={12} lg={8} key={s.name}>
            <Card title={s.name.toUpperCase()}>
              {s.asset_types.map((t2) => (
                <Tag key={t2} color="purple">
                  {t2}
                </Tag>
              ))}
            </Card>
          </Col>
        ))}
      </Row>

      <Title level={4} style={{ marginTop: 24 }}>
        {t.integrations.ai}
      </Title>
      <Card>
        <Paragraph>
          {ai?.enabled ? (
            <Tag color="green">{t.ai.enabled}</Tag>
          ) : (
            <Tag color="orange">{t.ai.disabled}</Tag>
          )}
        </Paragraph>
        <Paragraph type="secondary">
          <code>{ai?.model_default}</code> / <code>{ai?.model_deep}</code>
        </Paragraph>
      </Card>

      <Title level={4} style={{ marginTop: 24 }}>
        {t.integrations.mcp}
      </Title>
      <Card>
        <Paragraph>{t.integrations.mcpDesc}</Paragraph>

        <Text strong>{t.integrations.mcpStdio}</Text>
        <Paragraph type="secondary" style={{ marginBottom: 4 }}>
          Claude Desktop의 <code>~/Library/Application Support/Claude/claude_desktop_config.json</code>:
        </Paragraph>
        <pre
          style={{
            background: "#0d1421",
            padding: 12,
            borderRadius: 6,
            overflowX: "auto",
            border: "1px solid var(--mond-border)",
          }}
        >
{`{
  "mcpServers": {
    "mond": {
      "command": "python",
      "args": ["-m", "mcp_server"],
      "cwd": "/path/to/mond/backend",
      "env": {
        "DATABASE_URL": "postgresql+asyncpg://mond:mond@localhost:5432/mond",
        "ANTHROPIC_API_KEY": "sk-ant-..."
      }
    }
  }
}`}
        </pre>

        <Text strong style={{ marginTop: 12, display: "inline-block" }}>
          {t.integrations.mcpHttp}
        </Text>
        <Paragraph type="secondary">
          Backend가 <code>/mcp</code> 경로에 SSE 엔드포인트를 마운트합니다. 원격 클라이언트가 그
          엔드포인트를 가리키도록 설정하세요. <code>MCP_HTTP_ENABLED=false</code>로 끌 수 있습니다.
        </Paragraph>
      </Card>

      <Title level={4} style={{ marginTop: 24 }}>
        {t.integrations.notifications}
      </Title>
      <Card>
        <Paragraph>{t.integrations.notificationsDesc}</Paragraph>
        <Paragraph type="secondary">
          ENV: <code>SLACK_WEBHOOK_URL</code> · <code>GENERIC_WEBHOOK_URL</code> ·{" "}
          <code>NOTIFY_MIN_SEVERITY</code>
        </Paragraph>
      </Card>

      <Title level={4} style={{ marginTop: 24 }}>
        {t.integrations.webhookGithub}
      </Title>
      <Card>
        <Paragraph>{t.integrations.webhookGithubDesc}</Paragraph>
        <Alert
          type="info"
          showIcon
          message={
            <>
              GitHub 리포지토리 Settings → Webhooks →{" "}
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
    </div>
  );
}
