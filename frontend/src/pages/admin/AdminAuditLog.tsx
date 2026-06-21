/**
 * Admin · Audit Log — access_audit_logs 검색·필터·시계열 뷰 (ADMIN 전용).
 *
 * 필터: 기간 · actor · event · request_id.
 * 시계열 timeline 표 — actor + event 색 chip + detail JSON expand.
 */

import { FileSearchOutlined, ReloadOutlined } from "@ant-design/icons";
import { useQuery } from "@tanstack/react-query";
import {
  Button,
  Card,
  DatePicker,
  Empty,
  Input,
  Select,
  Space,
  Table,
  Tag,
  Typography,
} from "antd";
import type { Dayjs } from "dayjs";
import { useMemo, useState } from "react";

import { useI18n } from "@/i18n";
import { api } from "@/lib/api";

const { Title, Paragraph, Text } = Typography;
const { RangePicker } = DatePicker;

type AuditEvent =
  | "ai_decided"
  | "human_decided"
  | "granted"
  | "grant_failed"
  | "expired_revoked"
  | "revoke_failed"
  | "manual_revoked";

interface AuditRow {
  id: number;
  request_id: number;
  event: AuditEvent;
  actor: string;
  detail: Record<string, unknown>;
  created_at: string;
  request: null | {
    requester: string;
    identity_id: number;
    permission_id: number;
    status: string;
  };
}

interface AuditResp {
  items: AuditRow[];
  limit: number;
  offset: number;
  count: number;
}

const EVENT_COLOR: Record<AuditEvent, string> = {
  ai_decided: "purple",
  human_decided: "geekblue",
  granted: "green",
  grant_failed: "red",
  expired_revoked: "default",
  revoke_failed: "magenta",
  manual_revoked: "orange",
};

const EVENT_LABEL_KO: Record<AuditEvent, string> = {
  ai_decided: "AI 결정",
  human_decided: "담당자 결정",
  granted: "권한 부여",
  grant_failed: "부여 실패",
  expired_revoked: "만료 회수",
  revoke_failed: "회수 실패",
  manual_revoked: "수동 회수",
};

const EVENT_OPTIONS: AuditEvent[] = [
  "ai_decided",
  "human_decided",
  "granted",
  "grant_failed",
  "expired_revoked",
  "revoke_failed",
  "manual_revoked",
];

export default function AdminAuditLog() {
  const { locale } = useI18n();
  const [range, setRange] = useState<[Dayjs, Dayjs] | null>(null);
  const [actor, setActor] = useState("");
  const [event, setEvent] = useState<AuditEvent | undefined>(undefined);
  const [requestId, setRequestId] = useState("");

  const params = useMemo(() => {
    const p: Record<string, string | number> = { limit: 200 };
    if (range?.[0]) p.start = range[0].toISOString();
    if (range?.[1]) p.end = range[1].toISOString();
    if (actor.trim()) p.actor = actor.trim();
    if (event) p.event = event;
    const rid = Number(requestId);
    if (rid && Number.isFinite(rid)) p.request_id = rid;
    return p;
  }, [range, actor, event, requestId]);

  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ["admin-audit-log", params],
    queryFn: async () => (await api.get<AuditResp>("/admin/audit-log", { params })).data,
  });

  return (
    <div>
      <Title level={2} style={{ marginBottom: 8 }}>
        <Space>
          <FileSearchOutlined />
          <span>{locale === "ko" ? "감사 로그" : "Audit Log"}</span>
        </Space>
      </Title>
      <Paragraph type="secondary">
        {locale === "ko"
          ? "권한 요청 흐름의 모든 결정(AI/담당자), 부여, 회수 이벤트를 시계열로 검색합니다. ADMIN 권한 필요."
          : "Search access-request audit events (AI/human decisions, grants, revokes). ADMIN only."}
      </Paragraph>

      <Card style={{ marginBottom: 12 }}>
        <Space wrap size={[8, 8]}>
          <RangePicker
            showTime
            value={range ?? undefined}
            onChange={(v) => setRange(v as [Dayjs, Dayjs] | null)}
            allowClear
          />
          <Input
            placeholder={locale === "ko" ? "actor (이메일·system·ai)" : "actor email/system/ai"}
            value={actor}
            onChange={(e) => setActor(e.target.value)}
            style={{ width: 220 }}
            allowClear
          />
          <Select
            placeholder={locale === "ko" ? "event 전체" : "All events"}
            value={event}
            onChange={(v) => setEvent(v)}
            options={EVENT_OPTIONS.map((e) => ({
              value: e,
              label: (
                <Space size={4}>
                  <Tag color={EVENT_COLOR[e]} style={{ marginInlineEnd: 0 }}>
                    {EVENT_LABEL_KO[e]}
                  </Tag>
                </Space>
              ),
            }))}
            style={{ width: 200 }}
            allowClear
          />
          <Input
            placeholder="request_id"
            value={requestId}
            onChange={(e) => setRequestId(e.target.value.replace(/\D/g, ""))}
            style={{ width: 130 }}
            allowClear
          />
          <Button
            icon={<ReloadOutlined />}
            loading={isFetching}
            onClick={() => refetch()}
          >
            {locale === "ko" ? "새로고침" : "Refresh"}
          </Button>
        </Space>
      </Card>

      <Card>
        <Table
          loading={isLoading}
          dataSource={data?.items ?? []}
          rowKey="id"
          size="small"
          pagination={{ pageSize: 50, showSizeChanger: false }}
          locale={{
            emptyText: (
              <Empty
                description={
                  locale === "ko" ? "조건에 맞는 감사 이벤트가 없습니다" : "No audit events match"
                }
              />
            ),
          }}
          expandable={{
            rowExpandable: (r) => Object.keys(r.detail || {}).length > 0,
            expandedRowRender: (r) => (
              <pre
                style={{
                  background: "var(--mond-surface-2, #0d1421)",
                  padding: 10,
                  borderRadius: 6,
                  fontSize: 11,
                  marginBottom: 0,
                  overflowX: "auto",
                }}
              >
                {JSON.stringify(r.detail, null, 2)}
              </pre>
            ),
          }}
          columns={[
            {
              title: locale === "ko" ? "시각" : "When",
              dataIndex: "created_at",
              width: 180,
              render: (v: string) => (
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {new Date(v).toLocaleString()}
                </Text>
              ),
            },
            {
              title: "Event",
              dataIndex: "event",
              width: 140,
              render: (e: AuditEvent) => (
                <Tag color={EVENT_COLOR[e]} style={{ marginInlineEnd: 0 }}>
                  {EVENT_LABEL_KO[e]}
                </Tag>
              ),
            },
            {
              title: locale === "ko" ? "Actor" : "Actor",
              dataIndex: "actor",
              width: 220,
              render: (a: string) => {
                const isAi = a === "ai" || a === "claude";
                const isSystem = a === "system";
                return (
                  <Tag
                    color={isAi ? "purple" : isSystem ? "default" : "geekblue"}
                    style={{ marginInlineEnd: 0 }}
                  >
                    {a}
                  </Tag>
                );
              },
            },
            {
              title: "Request",
              dataIndex: "request_id",
              width: 130,
              render: (rid: number, r: AuditRow) => (
                <Space size={4}>
                  <Text strong>#{rid}</Text>
                  {r.request?.requester && (
                    <Text type="secondary" style={{ fontSize: 11 }}>
                      {r.request.requester}
                    </Text>
                  )}
                </Space>
              ),
            },
            {
              title: locale === "ko" ? "요약" : "Summary",
              key: "summary",
              render: (_: unknown, r: AuditRow) => {
                const d = r.detail || {};
                const bits: string[] = [];
                if (typeof d.decision === "string") bits.push(`decision=${d.decision}`);
                if (typeof d.risk_level === "string") bits.push(`risk=${d.risk_level}`);
                if (typeof d.reason === "string") bits.push(d.reason as string);
                if (bits.length === 0 && Object.keys(d).length > 0) {
                  return (
                    <Text type="secondary" style={{ fontSize: 11 }}>
                      {Object.keys(d).join(" · ")}
                    </Text>
                  );
                }
                return (
                  <Text type="secondary" style={{ fontSize: 12 }} ellipsis>
                    {bits.join(" · ")}
                  </Text>
                );
              },
            },
          ]}
        />
      </Card>
    </div>
  );
}
