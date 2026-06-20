/**
 * IAM Explorer — 가져온 Identity / Permission을 임직원이 알아보기 쉽게.
 *
 * 외부 시스템에서 import한 UUID·ARN·DN은 보조 정보로 두고, 사람이 읽는
 * 이름을 강조합니다. Source 필터 + 검색 + Permission 인라인 "권한 요청" CTA로
 * 신청 흐름을 1클릭에 연결합니다.
 */

import {
  CloudDownloadOutlined,
  PlusCircleOutlined,
  SafetyCertificateOutlined,
  SearchOutlined,
} from "@ant-design/icons";
import { useQuery } from "@tanstack/react-query";
import {
  Alert,
  Card,
  Col,
  Empty,
  Input,
  Row,
  Segmented,
  Space,
  Table,
  Tag,
  Tooltip,
  Typography,
} from "antd";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { useI18n } from "@/i18n";
import {
  iamApi,
  type IAMCapability,
  type IAMIdentity,
  type IAMSourceKind,
  type IdentityType,
  type PermissionRow,
} from "@/lib/iam-api";
import {
  IDENTITY_TYPE_COLOR,
  identityDisplay,
  identityMatches,
  permissionDisplay,
  permissionMatches,
} from "@/lib/iam-display";

const { Title, Paragraph, Text } = Typography;

const RISK_COLOR: Record<string, string> = {
  admin: "red",
  write: "orange",
  read: "green",
};

const STATUS_COLOR: Record<IAMCapability["status"], string> = {
  ready: "green",
  demo: "orange",
  coming_soon: "default",
};

const ALL = "__all__";

export default function IAMExplorer() {
  const { t, locale } = useI18n();

  const { data: sources } = useQuery({ queryKey: ["iam-sources"], queryFn: iamApi.listSources });
  const { data: identities } = useQuery({
    queryKey: ["iam-identities"],
    queryFn: () => iamApi.listIdentities(),
  });
  const { data: permissions } = useQuery({
    queryKey: ["iam-permissions"],
    queryFn: () => iamApi.listPermissions(),
  });
  const { data: capabilities } = useQuery({
    queryKey: ["iam-capabilities"],
    queryFn: iamApi.capabilities,
  });

  const [sourceFilter, setSourceFilter] = useState<string>(ALL);
  const [query, setQuery] = useState("");

  const capByKind = (k: IAMSourceKind): IAMCapability | undefined =>
    (capabilities ?? []).find((c) => c.kind === k);

  const sourceById = useMemo(() => {
    const m = new Map<number, { name: string; kind: IAMSourceKind }>();
    for (const s of sources ?? []) m.set(s.id, { name: s.name, kind: s.kind });
    return m;
  }, [sources]);

  const filteredIdentities = useMemo(() => {
    return (identities ?? [])
      .filter((i) => sourceFilter === ALL || String(i.source_id) === sourceFilter)
      .filter((i) => identityMatches(i, query));
  }, [identities, sourceFilter, query]);

  const filteredPermissions = useMemo(() => {
    return (permissions ?? [])
      .filter((p) => sourceFilter === ALL || String(p.source_id) === sourceFilter)
      .filter((p) => permissionMatches(p, query));
  }, [permissions, sourceFilter, query]);

  const sourceOptions = useMemo(() => {
    const all = { label: locale === "ko" ? `전체 (${sources?.length ?? 0})` : `All (${sources?.length ?? 0})`, value: ALL };
    const items = (sources ?? []).map((s) => ({
      label: (
        <Space size={4}>
          <Text strong>{s.name}</Text>
          <Tag style={{ marginInlineEnd: 0 }}>{s.kind.toUpperCase()}</Tag>
        </Space>
      ),
      value: String(s.id),
    }));
    return [all, ...items];
  }, [sources, locale]);

  return (
    <div>
      <Title level={2} style={{ marginBottom: 8 }}>
        {t.iam.iamExplorerTitle}
      </Title>
      <Paragraph type="secondary">{t.iam.iamExplorerDesc}</Paragraph>

      {/* 상단 필터 — 소스 segment + 검색 박스 */}
      <Card style={{ marginBottom: 12 }} styles={{ body: { paddingBlock: 12 } }}>
        <Space direction="vertical" size={8} style={{ width: "100%" }}>
          <div style={{ overflowX: "auto" }}>
            <Segmented
              value={sourceFilter}
              onChange={(v) => setSourceFilter(String(v))}
              options={sourceOptions}
            />
          </div>
          <Input
            allowClear
            prefix={<SearchOutlined />}
            placeholder={
              locale === "ko"
                ? "이름·ARN·이메일·역할 검색"
                : "Search by name, ARN, email, role"
            }
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </Space>
      </Card>

      {/* Sources 요약 — 정상 동작 여부와 마지막 동기화 시각 */}
      <Card title={locale === "ko" ? "연결된 IAM 소스" : "Connected IAM sources"} style={{ marginBottom: 16 }}>
        <Table
          dataSource={sources ?? []}
          rowKey="id"
          size="small"
          pagination={false}
          columns={[
            { title: "ID", dataIndex: "id", width: 60 },
            { title: t.iam.fields.source, dataIndex: "name" },
            {
              title: t.iam.fields.type,
              dataIndex: "kind",
              width: 220,
              render: (k: IAMSourceKind) => {
                const cap = capByKind(k);
                return (
                  <Space size={4} wrap>
                    <Tag>{k.toUpperCase()}</Tag>
                    {cap && (
                      <Tag color={STATUS_COLOR[cap.status]}>
                        {locale === "ko"
                          ? cap.status === "ready"
                            ? "정상 동작"
                            : cap.status === "demo"
                              ? "데모"
                              : "준비 중"
                          : cap.status}
                      </Tag>
                    )}
                  </Space>
                );
              },
            },
            {
              title: locale === "ko" ? "마지막 동기화" : "Last sync",
              dataIndex: "last_synced_at_str",
              render: (v: string | null) => v || "—",
            },
          ]}
        />
      </Card>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <IdentityCard
            identities={filteredIdentities}
            sourceById={sourceById}
            locale={locale}
            t={t}
          />
        </Col>
        <Col xs={24} lg={12}>
          <PermissionCard
            permissions={filteredPermissions}
            sourceById={sourceById}
            locale={locale}
          />
        </Col>
      </Row>

      <Alert
        type="info"
        showIcon
        style={{ marginTop: 16 }}
        message={
          locale === "ko"
            ? "외부 시스템(AWS · Azure · GCP · Kubernetes · 사내 LDAP/AD)에서 가져온 ARN·UUID·DN은 짧은 이름으로 보여주고, 원본 ID는 그 아래 회색으로 표기합니다. 짧은 이름에 마우스를 올리면 전체 ID가 나옵니다. AWS IAM Identity Center · Azure AD · Google Workspace 등 SSO로 들어온 사람은 자홍색 'SSO' 태그로 구분합니다."
            : "External system identifiers (ARN / UUID / DN from AWS · Azure · GCP · Kubernetes · LDAP) are shown as short names; the full ID is the gray line below. Hover the short name for the full ID. Federated identities imported from AWS IAM Identity Center / Azure AD / Google Workspace SSO carry a magenta 'SSO' tag."
        }
      />
    </div>
  );
}

function IdentityCard({
  identities,
  sourceById,
  locale,
  t,
}: {
  identities: IAMIdentity[];
  sourceById: Map<number, { name: string; kind: IAMSourceKind }>;
  locale: "ko" | "en";
  t: ReturnType<typeof useI18n>["t"];
}) {
  return (
    <Card
      title={
        <Space>
          <CloudDownloadOutlined />
          <span>{locale === "ko" ? "Identity (사용자·역할·서비스 계정·그룹)" : "Identities"}</span>
        </Space>
      }
      extra={<Tag color="cyan">{identities.length}</Tag>}
    >
      <Table
        dataSource={identities}
        rowKey="id"
        size="small"
        pagination={{ pageSize: 8, showSizeChanger: false }}
        locale={{ emptyText: <Empty description={locale === "ko" ? "검색 결과 없음" : "No matches"} /> }}
        columns={[
          {
            title: locale === "ko" ? "이름" : "Name",
            key: "name",
            render: (_, i) => {
              const d = identityDisplay(i);
              const src = sourceById.get(i.source_id);
              const isSso = i.identity_type === "sso_user" || i.identity_type === "sso_group";
              return (
                <Space direction="vertical" size={0} style={{ width: "100%" }}>
                  <Space size={6} wrap>
                    <Tooltip title={d.tooltip}>
                      <Text strong style={{ fontSize: 14 }}>{d.primary}</Text>
                    </Tooltip>
                    <Tag color={IDENTITY_TYPE_COLOR[i.identity_type as IdentityType]}>
                      {t.iam.identityTypes[i.identity_type as IdentityType]}
                    </Tag>
                    {isSso && <Tag color="magenta">SSO</Tag>}
                    {src && (
                      <Tag style={{ marginInlineEnd: 0 }}>
                        {src.kind.toUpperCase()} · {src.name}
                      </Tag>
                    )}
                  </Space>
                  {d.secondary && (
                    <Text type="secondary" style={{ fontSize: 12, fontFamily: "var(--mond-font-mono, monospace)" }} ellipsis>
                      {d.secondary}
                    </Text>
                  )}
                </Space>
              );
            },
          },
        ]}
      />
    </Card>
  );
}

function PermissionCard({
  permissions,
  sourceById,
  locale,
}: {
  permissions: PermissionRow[];
  sourceById: Map<number, { name: string; kind: IAMSourceKind }>;
  locale: "ko" | "en";
}) {
  return (
    <Card
      title={
        <Space>
          <SafetyCertificateOutlined />
          <span>{locale === "ko" ? "권한 (요청 가능한 단위)" : "Permissions"}</span>
        </Space>
      }
      extra={<Tag color="cyan">{permissions.length}</Tag>}
    >
      <Table
        dataSource={permissions}
        rowKey="id"
        size="small"
        pagination={{ pageSize: 8, showSizeChanger: false }}
        locale={{ emptyText: <Empty description={locale === "ko" ? "검색 결과 없음" : "No matches"} /> }}
        columns={[
          {
            title: locale === "ko" ? "권한 이름" : "Permission",
            key: "name",
            render: (_, p) => {
              const d = permissionDisplay(p);
              const src = sourceById.get(p.source_id);
              return (
                <Space direction="vertical" size={0} style={{ width: "100%" }}>
                  <Space size={6} wrap>
                    <Tooltip title={d.tooltip}>
                      <Text strong style={{ fontSize: 14 }}>{d.primary}</Text>
                    </Tooltip>
                    {p.risk_hint && (
                      <Tag color={RISK_COLOR[p.risk_hint] ?? "default"}>
                        {p.risk_hint.toUpperCase()}
                      </Tag>
                    )}
                    {src && (
                      <Tag style={{ marginInlineEnd: 0 }}>
                        {src.kind.toUpperCase()} · {src.name}
                      </Tag>
                    )}
                  </Space>
                  {p.description && (
                    <Text type="secondary" style={{ fontSize: 12 }} ellipsis>
                      {p.description}
                    </Text>
                  )}
                  {d.secondary && (
                    <Text type="secondary" style={{ fontSize: 12, fontFamily: "var(--mond-font-mono, monospace)" }} ellipsis>
                      {d.secondary}
                    </Text>
                  )}
                </Space>
              );
            },
          },
          {
            title: "",
            key: "action",
            width: 110,
            render: (_, p) => (
              <Link to={`/access-center?permission_id=${p.id}&source_id=${p.source_id}`}>
                <Tooltip title={locale === "ko" ? "이 권한을 신청합니다" : "Request this permission"}>
                  <Tag
                    color="blue"
                    style={{ cursor: "pointer", marginInlineEnd: 0 }}
                    icon={<PlusCircleOutlined />}
                  >
                    {locale === "ko" ? "권한 요청" : "Request"}
                  </Tag>
                </Tooltip>
              </Link>
            ),
          },
        ]}
      />
    </Card>
  );
}
