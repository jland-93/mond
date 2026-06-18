/**
 * GitHub Webhook 설정 안내 카드.
 */

import { ApiOutlined } from "@ant-design/icons";
import { Alert, Card, Space, Typography } from "antd";

import { useI18n } from "@/i18n";

const { Paragraph } = Typography;

export default function WebhookCard() {
  const { t } = useI18n();

  return (
    <Card
      title={
        <Space>
          <ApiOutlined />
          <span>{t.adminArea.webhookTitle}</span>
        </Space>
      }
    >
      <Paragraph type="secondary">{t.adminArea.webhookDesc}</Paragraph>
      <Alert
        type="info"
        showIcon
        message={
          <>
            GitHub Settings → Webhooks →{" "}
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
  );
}
