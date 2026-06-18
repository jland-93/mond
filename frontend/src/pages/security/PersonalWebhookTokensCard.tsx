/**
 * Personal Webhook Tokens — CI/CD가 사용자 세션 없이 스캔을 트리거할 수 있게.
 * raw 토큰은 발급 직후 한 번만 노출. 자산을 선택해 GitHub Actions / GitLab CI 스니펫 생성.
 */

import { ApiOutlined, CopyOutlined, DeleteOutlined, PlusOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  Button,
  Card,
  Empty,
  Input,
  Modal,
  Popconfirm,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from "antd";
import { useState } from "react";

import { useI18n } from "@/i18n";
import { api, type Asset, type Page } from "@/lib/api";
import {
  webhookTokensApi,
  type WebhookTokenCreated,
  type WebhookTokenRow,
} from "@/lib/webhook-tokens-api";

import SnippetBlock from "./SnippetBlock";

const { Paragraph, Text } = Typography;

export default function PersonalWebhookTokensCard() {
  const { locale } = useI18n();
  const qc = useQueryClient();
  const { data: tokens } = useQuery({ queryKey: ["webhook-tokens"], queryFn: webhookTokensApi.list });
  const { data: assets } = useQuery({
    queryKey: ["assets-lite-webhook"],
    queryFn: async () => {
      const { data } = await api.get<Page<Asset>>("/assets", { params: { limit: 200 } });
      return data.items;
    },
  });

  const [issueOpen, setIssueOpen] = useState(false);
  const [tokenName, setTokenName] = useState("");
  const [created, setCreated] = useState<WebhookTokenCreated | null>(null);
  const [snippetAsset, setSnippetAsset] = useState<number | null>(null);
  const [snippet, setSnippet] = useState<{ gh: string; gl: string; name: string } | null>(null);

  const issue = useMutation({
    mutationFn: (name: string) => webhookTokensApi.create(name),
    onSuccess: (data) => {
      setCreated(data);
      setIssueOpen(false);
      setTokenName("");
      qc.invalidateQueries({ queryKey: ["webhook-tokens"] });
    },
    onError: (e: Error & { response?: { data?: { detail?: string } } }) => {
      message.error(e.response?.data?.detail ?? e.message);
    },
  });

  const revoke = useMutation({
    mutationFn: (id: number) => webhookTokensApi.revoke(id),
    onSuccess: () => {
      message.success(locale === "ko" ? "회수됨" : "Revoked");
      qc.invalidateQueries({ queryKey: ["webhook-tokens"] });
    },
  });

  const loadSnippet = useMutation({
    mutationFn: (assetId: number) => webhookTokensApi.snippet(assetId),
    onSuccess: (data) => {
      setSnippet({ gh: data.github_actions, gl: data.gitlab_ci, name: data.asset_name });
    },
  });

  const active = (tokens ?? []).filter((t) => !t.revoked_at);

  return (
    <Card
      title={
        <Space>
          <ApiOutlined />
          <span>{locale === "ko" ? "Personal Webhook Tokens" : "Personal Webhook Tokens"}</span>
          {active.length > 0 && <Tag color="green">{active.length}</Tag>}
        </Space>
      }
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setIssueOpen(true)}>
          {locale === "ko" ? "토큰 발급" : "Issue token"}
        </Button>
      }
      style={{ marginTop: 16 }}
    >
      <Paragraph type="secondary">
        {locale === "ko"
          ? "사내 CI/CD가 사용자 세션 없이 Mond에 스캔을 트리거할 수 있게 발급. raw 토큰은 발급 직후 한 번만 노출됩니다."
          : "Issue tokens so CI/CD can trigger scans without a user session. Raw token is shown only once."}
      </Paragraph>

      {(tokens ?? []).length === 0 ? (
        <Empty description={locale === "ko" ? "발급된 토큰이 없습니다" : "No tokens"} />
      ) : (
        <Table
          size="small"
          pagination={false}
          dataSource={tokens ?? []}
          rowKey="id"
          columns={[
            { title: locale === "ko" ? "라벨" : "Label", dataIndex: "name" },
            {
              title: locale === "ko" ? "토큰" : "Token",
              dataIndex: "token_prefix",
              render: (v: string) => <code className="mond-mono">{v}••••</code>,
              width: 200,
            },
            {
              title: locale === "ko" ? "최근 사용" : "Last used",
              dataIndex: "last_used_at",
              render: (v: string | null) => (v ? v.slice(0, 19).replace("T", " ") : "—"),
              width: 180,
            },
            {
              title: locale === "ko" ? "상태" : "Status",
              dataIndex: "revoked_at",
              render: (v: string | null) =>
                v ? (
                  <Tag color="default">{locale === "ko" ? "회수됨" : "Revoked"}</Tag>
                ) : (
                  <Tag color="green">{locale === "ko" ? "활성" : "Active"}</Tag>
                ),
              width: 100,
            },
            {
              title: "",
              width: 60,
              render: (_: unknown, r: WebhookTokenRow) =>
                r.revoked_at ? null : (
                  <Popconfirm
                    title={locale === "ko" ? "이 토큰을 회수할까요?" : "Revoke this token?"}
                    okType="danger"
                    onConfirm={() => revoke.mutate(r.id)}
                  >
                    <Button size="small" type="text" danger icon={<DeleteOutlined />} />
                  </Popconfirm>
                ),
            },
          ]}
        />
      )}

      <Modal
        open={!!created}
        title={locale === "ko" ? "토큰 발급됨 — 한 번만 표시됩니다" : "Token issued — shown only once"}
        onOk={() => setCreated(null)}
        onCancel={() => setCreated(null)}
        okText={locale === "ko" ? "저장했어요" : "I saved it"}
        cancelButtonProps={{ style: { display: "none" } }}
      >
        <Alert
          type="warning"
          showIcon
          message={
            locale === "ko"
              ? "이 토큰은 다시 표시되지 않습니다. CI 시크릿에 즉시 등록하세요."
              : "This token will not be shown again. Save it to CI secrets immediately."
          }
          style={{ marginBottom: 12 }}
        />
        <Input.TextArea
          value={created?.raw_token ?? ""}
          rows={2}
          readOnly
          style={{ fontFamily: "monospace" }}
        />
        <Button
          icon={<CopyOutlined />}
          style={{ marginTop: 8 }}
          onClick={async () => {
            await navigator.clipboard.writeText(created?.raw_token ?? "");
            message.success(locale === "ko" ? "클립보드에 복사됨" : "Copied");
          }}
        >
          {locale === "ko" ? "복사" : "Copy"}
        </Button>
      </Modal>

      <Modal
        open={issueOpen}
        title={locale === "ko" ? "Webhook 토큰 발급" : "Issue webhook token"}
        onOk={() => issue.mutate(tokenName.trim() || "CI token")}
        onCancel={() => setIssueOpen(false)}
        confirmLoading={issue.isPending}
        okText={locale === "ko" ? "발급" : "Issue"}
      >
        <Paragraph type="secondary">
          {locale === "ko"
            ? "이 토큰을 어디에 사용할지 알아볼 수 있게 라벨을 적어 주세요."
            : "Give the token a label so you remember where it's used."}
        </Paragraph>
        <Input
          autoFocus
          value={tokenName}
          onChange={(e) => setTokenName(e.target.value)}
          placeholder="GitHub Actions · main repo"
          maxLength={120}
        />
      </Modal>

      <div style={{ marginTop: 16, padding: 12, background: "var(--mond-surface-2)", borderRadius: 8 }}>
        <Space direction="vertical" style={{ width: "100%" }}>
          <Text strong>{locale === "ko" ? "CI/CD 스니펫 생성" : "Generate CI/CD snippet"}</Text>
          <Paragraph type="secondary" style={{ marginBottom: 4 }}>
            {locale === "ko"
              ? "자산을 선택하면 GitHub Actions와 GitLab CI에 그대로 붙여넣을 수 있는 YAML이 생성됩니다."
              : "Pick an asset to get drop-in YAML for GitHub Actions and GitLab CI."}
          </Paragraph>
          <Space>
            <Select
              showSearch
              optionFilterProp="label"
              placeholder={locale === "ko" ? "자산 선택" : "Pick an asset"}
              value={snippetAsset ?? undefined}
              onChange={setSnippetAsset}
              style={{ width: 360 }}
              options={(assets ?? []).map((a) => ({
                value: a.id,
                label: `${a.name} (${a.asset_type})`,
              }))}
            />
            <Button
              type="primary"
              disabled={!snippetAsset}
              onClick={() => snippetAsset && loadSnippet.mutate(snippetAsset)}
              loading={loadSnippet.isPending}
            >
              {locale === "ko" ? "스니펫 생성" : "Generate"}
            </Button>
          </Space>
        </Space>
      </div>

      <Modal
        open={!!snippet}
        onCancel={() => setSnippet(null)}
        onOk={() => setSnippet(null)}
        okText={locale === "ko" ? "닫기" : "Close"}
        cancelButtonProps={{ style: { display: "none" } }}
        width={720}
        title={
          locale === "ko"
            ? `"${snippet?.name}" — CI/CD 스니펫`
            : `"${snippet?.name}" — CI/CD snippet`
        }
      >
        <Alert
          type="info"
          showIcon
          style={{ marginBottom: 12 }}
          message={
            locale === "ko"
              ? "CI Secrets에 MOND_WEBHOOK_TOKEN(raw 토큰) + MOND_HOST(예: mond.your-corp.com) 두 개를 먼저 등록하세요."
              : "Register MOND_WEBHOOK_TOKEN (raw token) and MOND_HOST in your CI secrets first."
          }
        />
        {snippet && (
          <Space direction="vertical" style={{ width: "100%" }} size="middle">
            <SnippetBlock label="GitHub Actions" content={snippet.gh} />
            <SnippetBlock label="GitLab CI" content={snippet.gl} />
          </Space>
        )}
      </Modal>
    </Card>
  );
}
