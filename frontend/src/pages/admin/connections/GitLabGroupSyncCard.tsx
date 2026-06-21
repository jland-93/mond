/**
 * GitLab group/user → Mond Asset 일괄 동기화 카드.
 * GitHubOrgSyncCard와 톤·동작 동일. self-host GitLab은 GITLAB_API_URL ENV로.
 */

import { GitlabOutlined, SyncOutlined } from "@ant-design/icons";
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
  default_group: string | null;
  api_url: string;
}

interface RunResp {
  discovered: number;
  created: number;
  updated: number;
  skipped_archived: number;
  dry_run: boolean;
  group: string;
  repos: Array<{ name: string; visibility: string; default_branch: string; action: string }>;
}

export default function GitLabGroupSyncCard() {
  const { locale } = useI18n();
  const [group, setGroup] = useState("");
  const [includeArchived, setIncludeArchived] = useState(false);
  const [lastResult, setLastResult] = useState<RunResp | null>(null);

  const { data: status } = useQuery({
    queryKey: ["gitlab-sync-status"],
    queryFn: async () => (await api.get<StatusResp>("/admin/gitlab-sync/status")).data,
  });

  useEffect(() => {
    if (status?.default_group && !group) setGroup(status.default_group);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status?.default_group]);

  const run = useMutation({
    mutationFn: async (dry: boolean) => {
      const { data } = await api.post<RunResp>("/admin/gitlab-sync/run", {
        group,
        dry_run: dry,
        include_archived: includeArchived,
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
          <GitlabOutlined style={{ color: "#fc6d26" }} />
          <span>{locale === "ko" ? "GitLab 자산 동기화" : "GitLab Group Asset Sync"}</span>
        </Space>
      }
      style={{ marginBottom: 16 }}
    >
      <Paragraph type="secondary" style={{ marginBottom: 12 }}>
        {locale === "ko"
          ? "GitLab group의 모든 project(sub-group 포함)를 Mond Asset으로 등록합니다. self-host GitLab은 GITLAB_API_URL ENV로 지정."
          : "Sync every project in a GitLab group (sub-groups included) as Mond Asset. Self-hosted GitLab via GITLAB_API_URL."}
      </Paragraph>

      <Space.Compact style={{ width: "100%", marginBottom: 8 }}>
        <Input
          placeholder={locale === "ko" ? "group (예: my-org 또는 my-org/sub)" : "group (e.g. my-org or my-org/sub)"}
          value={group}
          onChange={(e) => setGroup(e.target.value)}
        />
        <Button
          icon={<SyncOutlined />}
          loading={run.isPending && run.variables === true}
          onClick={() => run.mutate(true)}
          disabled={!group}
        >
          {locale === "ko" ? "미리보기" : "Dry-run"}
        </Button>
        <Button
          type="primary"
          icon={<SyncOutlined />}
          loading={run.isPending && run.variables === false}
          onClick={() => run.mutate(false)}
          disabled={!group}
        >
          {locale === "ko" ? "동기화" : "Sync"}
        </Button>
      </Space.Compact>

      <Checkbox checked={includeArchived} onChange={(e) => setIncludeArchived(e.target.checked)}>
        {locale === "ko" ? "archived project도 포함" : "Include archived projects"}
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
                    <Tag
                      color={
                        item.visibility === "public"
                          ? "green"
                          : item.visibility === "internal"
                            ? "geekblue"
                            : "orange"
                      }
                    >
                      {item.visibility}
                    </Tag>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {item.default_branch}
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
        type={status?.token_configured ? "info" : "warning"}
        showIcon
        style={{ marginTop: 12 }}
        message={
          <Text style={{ fontSize: 12 }}>
            {status?.token_configured ? (
              locale === "ko" ? (
                <>
                  <code>GITLAB_TOKEN</code> 활성 — private project 포함 가능. API: <code>{status.api_url}</code>
                </>
              ) : (
                <>
                  <code>GITLAB_TOKEN</code> active — private projects visible. API: <code>{status.api_url}</code>
                </>
              )
            ) : locale === "ko" ? (
              <>
                <code>GITLAB_TOKEN</code> 미설정 — public project만 보입니다. <code>.env</code>에서 설정 권장.
              </>
            ) : (
              <>
                <code>GITLAB_TOKEN</code> not set — public projects only. Configure in <code>.env</code>.
              </>
            )}
          </Text>
        }
      />
    </Card>
  );
}
