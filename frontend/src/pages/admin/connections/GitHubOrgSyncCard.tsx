import { GithubOutlined, SyncOutlined } from "@ant-design/icons";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  Alert,
  Button,
  Card,
  Checkbox,
  Input,
  List,
  Space,
  Statistic,
  Tag,
  Typography,
  message,
} from "antd";
import { useEffect, useState } from "react";

import { useI18n } from "@/i18n";
import { api } from "@/lib/api";

const { Paragraph, Text } = Typography;

interface StatusResp {
  token_configured: boolean;
  default_org: string | null;
}

interface RunResp {
  discovered: number;
  created: number;
  updated: number;
  skipped_archived: number;
  dry_run: boolean;
  org: string;
  repos: Array<{ name: string; private: boolean; language: string; action: string }>;
}

export default function GitHubOrgSyncCard() {
  const { locale } = useI18n();
  const [org, setOrg] = useState("");
  const [includeArchived, setIncludeArchived] = useState(false);
  const [lastResult, setLastResult] = useState<RunResp | null>(null);

  const { data: status } = useQuery({
    queryKey: ["github-sync-status"],
    queryFn: async () => (await api.get<StatusResp>("/admin/github-sync/status")).data,
  });

  // status 받은 후 org 기본값 1회만 채움
  useEffect(() => {
    if (status?.default_org && !org) setOrg(status.default_org);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status?.default_org]);

  const run = useMutation({
    mutationFn: async (dry: boolean) => {
      const { data } = await api.post<RunResp>("/admin/github-sync/run", {
        org,
        dry_run: dry,
        include_archived: includeArchived,
      });
      return data;
    },
    onSuccess: (r) => {
      setLastResult(r);
      if (r.dry_run) {
        message.info(
          locale === "ko"
            ? `미리보기 — 등록 예정 ${r.created}, 업데이트 ${r.updated}`
            : `Preview — to create ${r.created}, to update ${r.updated}`,
        );
      } else {
        message.success(
          locale === "ko"
            ? `동기화 완료 — 신규 ${r.created}, 갱신 ${r.updated}`
            : `Synced — created ${r.created}, updated ${r.updated}`,
        );
      }
    },
    onError: (e: Error) => message.error(e.message),
  });

  const r = lastResult;

  return (
    <Card
      title={
        <Space>
          <GithubOutlined />
          <span>{locale === "ko" ? "GitHub org 자산 동기화" : "GitHub Org Asset Sync"}</span>
        </Space>
      }
      style={{ marginBottom: 16 }}
    >
      <Paragraph type="secondary" style={{ marginBottom: 12 }}>
        {locale === "ko"
          ? "GitHub org 또는 사용자의 모든 repo를 Mond Asset으로 등록합니다. 같은 URI는 라벨만 갱신, 사용자가 수정한 owner/environment는 보존."
          : "Register every repo in a GitHub org/user as Mond Asset. Re-running only refreshes sync-managed labels; owner/environment edits are preserved."}
      </Paragraph>

      <Space.Compact style={{ width: "100%", marginBottom: 8 }}>
        <Input
          placeholder={locale === "ko" ? "org 또는 user 이름 (예: jland-93)" : "org or user (e.g. jland-93)"}
          value={org}
          onChange={(e) => setOrg(e.target.value)}
        />
        <Button
          icon={<SyncOutlined />}
          loading={run.isPending && run.variables === true}
          onClick={() => run.mutate(true)}
          disabled={!org}
        >
          {locale === "ko" ? "미리보기" : "Dry-run"}
        </Button>
        <Button
          type="primary"
          icon={<SyncOutlined />}
          loading={run.isPending && run.variables === false}
          onClick={() => run.mutate(false)}
          disabled={!org}
        >
          {locale === "ko" ? "동기화" : "Sync"}
        </Button>
      </Space.Compact>

      <Checkbox checked={includeArchived} onChange={(e) => setIncludeArchived(e.target.checked)}>
        {locale === "ko" ? "archived repo도 포함" : "Include archived repos"}
      </Checkbox>

      {r && (
        <div style={{ marginTop: 16 }}>
          <Space size="large" style={{ marginBottom: 12 }}>
            <Statistic title={locale === "ko" ? "발견" : "Discovered"} value={r.discovered} />
            <Statistic title={locale === "ko" ? "신규" : "Created"} value={r.created} />
            <Statistic title={locale === "ko" ? "갱신" : "Updated"} value={r.updated} />
            <Statistic title={locale === "ko" ? "스킵(archived)" : "Skipped"} value={r.skipped_archived} />
          </Space>
          {r.repos.length > 0 && (
            <List
              size="small"
              header={
                <Text strong>
                  {r.dry_run
                    ? locale === "ko"
                      ? "미리보기"
                      : "Preview"
                    : locale === "ko"
                      ? "결과"
                      : "Result"}{" "}
                  ({r.repos.length})
                </Text>
              }
              dataSource={r.repos.slice(0, 30)}
              renderItem={(item) => (
                <List.Item>
                  <Space>
                    <Tag
                      color={
                        item.action === "create"
                          ? "green"
                          : item.action === "update"
                            ? "blue"
                            : "default"
                      }
                    >
                      {item.action}
                    </Tag>
                    <Text>{item.name}</Text>
                    {item.private && <Tag color="orange">private</Tag>}
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {item.language}
                    </Text>
                  </Space>
                </List.Item>
              )}
              footer={
                r.repos.length > 30 ? (
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {locale === "ko"
                      ? `상위 30개만 표시 (총 ${r.repos.length}개)`
                      : `Showing top 30 of ${r.repos.length}`}
                  </Text>
                ) : null
              }
            />
          )}
        </div>
      )}

      <Alert
        type={status?.token_configured ? "info" : "warning"}
        showIcon
        style={{ marginTop: 12 }}
        message={
          <Text style={{ fontSize: 12 }}>
            {status?.token_configured ? (
              locale === "ko" ? (
                <>
                  <code>GITHUB_TOKEN</code> 활성 — private repo 포함 가능. rate limit 5000/h.
                </>
              ) : (
                <>
                  <code>GITHUB_TOKEN</code> active — private repos visible. 5000 req/h.
                </>
              )
            ) : locale === "ko" ? (
              <>
                <code>GITHUB_TOKEN</code> 미설정 — public repo만 보이고 rate limit 60/h. <code>.env</code>에서 설정 권장.
              </>
            ) : (
              <>
                <code>GITHUB_TOKEN</code> not set — public repos only, 60 req/h. Configure in <code>.env</code>.
              </>
            )}
          </Text>
        }
      />
    </Card>
  );
}
