/**
 * 코드 스니펫 1개 블록 — label + copy 버튼 + pre.
 */

import { CopyOutlined } from "@ant-design/icons";
import { Button, Space, Typography, message } from "antd";

const { Text } = Typography;

interface Props {
  label: string;
  content: string;
}

export default function SnippetBlock({ label, content }: Props) {
  return (
    <div>
      <Space style={{ marginBottom: 6 }}>
        <Text strong>{label}</Text>
        <Button
          size="small"
          icon={<CopyOutlined />}
          onClick={async () => {
            await navigator.clipboard.writeText(content);
            message.success("Copied");
          }}
        >
          Copy
        </Button>
      </Space>
      <pre
        className="mond-mono"
        style={{
          background: "var(--mond-surface-0)",
          padding: 12,
          borderRadius: 8,
          fontSize: 12,
          margin: 0,
          whiteSpace: "pre-wrap",
        }}
      >
        {content}
      </pre>
    </div>
  );
}
