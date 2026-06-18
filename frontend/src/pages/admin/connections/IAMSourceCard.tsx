/**
 * IAM Source 카드 — 등록된 IAM source 목록과 동기화 액션.
 */

import { CloudOutlined, PlusOutlined, SyncOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button, Card, Space, Table, Tag, message } from "antd";

import { useI18n } from "@/i18n";
import { iamApi, type IAMCapability, type IAMSource, type IAMSourceKind } from "@/lib/iam-api";

import { KIND_LABEL, STATUS_COLOR, STATUS_LABEL_EN, STATUS_LABEL_KO } from "./constants";

interface Props {
  onAdd: () => void;
}

export default function IAMSourceCard({ onAdd }: Props) {
  const { t, locale } = useI18n();
  const qc = useQueryClient();

  const { data: sources } = useQuery({ queryKey: ["admin-iam-sources"], queryFn: iamApi.listSources });
  const { data: capabilities } = useQuery({ queryKey: ["iam-capabilities"], queryFn: iamApi.capabilities });

  const capByKind = (k: IAMSourceKind): IAMCapability | undefined =>
    (capabilities ?? []).find((c) => c.kind === k);

  const sync = useMutation({
    mutationFn: (id: number) => iamApi.syncSource(id),
    onSuccess: (data) => {
      message.success(
        `${(data.imported_identities as number) ?? 0} identities · ${
          (data.imported_permissions as number) ?? 0
        } permissions`,
      );
      qc.invalidateQueries({ queryKey: ["admin-iam-sources"] });
      qc.invalidateQueries({ queryKey: ["iam-identities"] });
      qc.invalidateQueries({ queryKey: ["iam-permissions"] });
    },
  });

  return (
    <Card
      title={
        <Space>
          <CloudOutlined />
          <span>{t.adminArea.iamSources}</span>
        </Space>
      }
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={onAdd}>
          {t.iam.addSource}
        </Button>
      }
      style={{ marginBottom: 16 }}
    >
      <Table
        dataSource={sources ?? []}
        rowKey="id"
        size="small"
        pagination={false}
        columns={[
          { title: "ID", dataIndex: "id", width: 60 },
          { title: t.common.name, dataIndex: "name" },
          {
            title: t.common.type,
            dataIndex: "kind",
            render: (k: IAMSourceKind) => {
              const cap = capByKind(k);
              return (
                <Space size={4} wrap>
                  <Tag color="purple">{KIND_LABEL[k] ?? k.toUpperCase()}</Tag>
                  {cap && (
                    <Tag color={STATUS_COLOR[cap.status]}>
                      {locale === "ko" ? STATUS_LABEL_KO[cap.status] : STATUS_LABEL_EN[cap.status]}
                    </Tag>
                  )}
                </Space>
              );
            },
            width: 240,
          },
          {
            title: "last sync",
            dataIndex: "last_synced_at_str",
            render: (v: string | null) => v || "—",
          },
          {
            title: t.iam.sync,
            render: (_: unknown, r: IAMSource) => (
              <Button size="small" icon={<SyncOutlined />} onClick={() => sync.mutate(r.id)}>
                {t.iam.syncSource}
              </Button>
            ),
            width: 140,
          },
        ]}
      />
    </Card>
  );
}
