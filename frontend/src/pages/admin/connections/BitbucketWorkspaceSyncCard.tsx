/**
 * Bitbucket workspace → Mond Asset 일괄 동기화 카드.
 * 인증은 username + app password (Atlassian 표준).
 */

import { SyncOutlined } from "@ant-design/icons";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  Alert,
  Button,
  Card,
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
  credentials_configured: boolean;
  default_workspace: string | null;
}

interface RunResp {
  discovered: number;
  created: number;
  updated: number;
  skipped_archived: number;
  dry_run: boolean;
  workspace: string;
  repos: Array<{ name: string; is_private: boolean; language: string; action: string }>;
}

export default function BitbucketWorkspaceSyncCard() {
  const { locale } = useI18n();
  const [workspace, setWorkspace] = useState("");
  const [lastResult, setLastResult] = useState<RunResp | null>(null);

  const { data: status } = useQuery({
    queryKey: ["bitbucket-sync-status"],
    queryFn: async () => (await api.get<StatusResp>("/admin/bitbucket-sync/status")).data,
  });

  useEffect(() => {
    if (status?.default_workspace && !workspace) setWorkspace(status.default_workspace);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status?.default_workspace]);

  const run = useMutation({
    mutationFn: async (dry: boolean) => {
      const { data } = await api.post<RunResp>("/admin/bitbucket-sync/run", {
        workspace,
        dry_run: dry,
      });
      return data;
    },
    onSuccess: (r) => {
      setLastResult(r);
      message[r.dry_run ? "info" : "success"](
        locale === "ko"
          ? `${r.dry_run ? "미리보기" : "동기화 완료"} — 신규 ${r.created}, 갱신 ${r.updated}`
          : `${r.dry_run ? "Preview" : "Synced"} — created ${r.created}, updated ${r.updated}`,
      );
    },
    onError: (e: Error) => message.error(e.message),
  });

  const r = lastResult;

  return (
    <Card
      title={
        <Space>
          <span style={{ color: "#2684ff", fontWeight: 700 }}>BB</span>
          <span>{locale === "ko" ? "Bitbucket 자산 동기화" : "Bitbucket Workspace Asset Sync"}</span>
        </Space>
      }
      style={{ marginBottom: 16 }}
    >
      <Paragraph type="secondary" style={{ marginBottom: 12 }}>
        {locale === "ko"
          ? "Bitbucket Cloud workspace의 모든 repository를 Mond Asset으로 등록합니다. 인증은 username + app password."
          : "Sync every repository in a Bitbucket Cloud workspace as Mond Asset. Auth: username + app password."}
      </Paragraph>

      <Space.Compact style={{ width: "100%", marginBottom: 8 }}>
        <Input
          placeholder={locale === "ko" ? "workspace (예: my-team)" : "workspace (e.g. my-team)"}
          value={workspace}
          onChange={(e) => setWorkspace(e.target.value)}
        />
        <Button
          icon={<SyncOutlined />}
          loading={run.isPending && run.variables === true}
          onClick={() => run.mutate(true)}
          disabled={!workspace}
        >
          {locale === "ko" ? "미리보기" : "Dry-run"}
        </Button>
        <Button
          type="primary"
          icon={<SyncOutlined />}
          loading={run.isPending && run.variables === false}
          onClick={() => run.mutate(false)}
          disabled={!workspace}
        >
          {locale === "ko" ? "동기화" : "Sync"}
        </Button>
      </Space.Compact>

      {r && (
        <div style={{ marginTop: 16 }}>
          <Space size="large" style={{ marginBottom: 12 }}>
            <Statistic title={locale === "ko" ? "발견" : "Discovered"} value={r.discovered} />
            <Statistic title={locale === "ko" ? "신규" : "Created"} value={r.created} />
            <Statistic title={locale === "ko" ? "갱신" : "Updated"} value={r.updated} />
          </Space>
          {r.repos.length > 0 && (
            <List
              size="small"
              header={
                <Text strong>
                  {(r.dry_run ? (locale === "ko" ? "미리보기" : "Preview") : (locale === "ko" ? "결과" : "Result"))} ({r.repos.length})
                </Text>
              }
              dataSource={r.repos.slice(0, 30)}
              renderItem={(item) => (
                <List.Item>
                  <Space>
                    <Tag
                      color={
                        item.action === "create" ? "green" : item.action === "update" ? "blue" : "default"
                      }
                    >
                      {item.action}
                    </Tag>
                    <Text>{item.name}</Text>
                    {item.is_private && <Tag color="orange">private</Tag>}
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {item.language}
                    </Text>
                  </Space>
                </List.Item>
              )}
              footer={
                r.repos.length > 30 ? (
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {locale === "ko" ? `상위 30개만 표시 (총 ${r.repos.length}개)` : `Showing top 30 of ${r.repos.length}`}
                  </Text>
                ) : null
              }
            />
          )}
        </div>
      )}

      <Alert
        type={status?.credentials_configured ? "info" : "warning"}
        showIcon
        style={{ marginTop: 12 }}
        message={
          <Text style={{ fontSize: 12 }}>
            {status?.credentials_configured ? (
              locale === "ko" ? (
                <>
                  <code>BITBUCKET_USERNAME</code> · <code>BITBUCKET_APP_PASSWORD</code> 활성 — private repo 포함 가능.
                </>
              ) : (
                <>
                  <code>BITBUCKET_USERNAME</code> · <code>BITBUCKET_APP_PASSWORD</code> active — private repos visible.
                </>
              )
            ) : locale === "ko" ? (
              <>
                자격증명 미설정 — public repo만 보입니다. <code>.env</code>에서 설정 권장.
              </>
            ) : (
              <>
                Credentials not set — public repos only. Configure in <code>.env</code>.
              </>
            )}
          </Text>
        }
      />
    </Card>
  );
}
