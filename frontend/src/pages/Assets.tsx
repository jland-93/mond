/**
 * Assets — 자산 인벤토리
 *
 * owner 컬럼은 inline 편집. 내 이메일과 같으면 강조 + '내 자산' 칩.
 * owner가 비어 있으면 '담당자 미정' + '내 자산으로 등록' 1클릭 버튼.
 * MyMond의 '자산 보기' CTA에서 진입한 사용자가 본인 owner를 1초에 등록.
 */

import { PlusOutlined, UserAddOutlined, UserOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Button,
  Form,
  Input,
  Modal,
  Popover,
  Select,
  Space,
  Table,
  Tag,
  Tooltip,
  Typography,
  message,
} from "antd";
import { useState } from "react";

import { useAuth } from "@/auth/AuthContext";
import { useI18n } from "@/i18n";
import { api, type Asset, type AssetType, type Page } from "@/lib/api";

const { Title, Text } = Typography;

const ASSET_TYPES: AssetType[] = [
  "repository",
  "container_image",
  "host",
  "url",
  "cloud_resource",
  "application",
];

async function fetchAssets(): Promise<Page<Asset>> {
  const { data } = await api.get<Page<Asset>>("/assets", { params: { limit: 100 } });
  return data;
}

export default function Assets() {
  const { t, locale } = useI18n();
  const { user } = useAuth();
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm();

  const { data, isLoading } = useQuery({
    queryKey: ["assets"],
    queryFn: fetchAssets,
  });

  const create = useMutation({
    mutationFn: (payload: Partial<Asset>) => api.post<Asset>("/assets", payload),
    onSuccess: () => {
      message.success(locale === "ko" ? "자산이 추가되었습니다." : "Asset added.");
      qc.invalidateQueries({ queryKey: ["assets"] });
      qc.invalidateQueries({ queryKey: ["me-overview"] });
      setOpen(false);
      form.resetFields();
    },
    onError: (err) => message.error((locale === "ko" ? "추가 실패: " : "Failed: ") + err.message),
  });

  const updateOwner = useMutation({
    mutationFn: ({ id, owner }: { id: number; owner: string | null }) =>
      api.patch<Asset>(`/assets/${id}`, { owner }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["assets"] });
      qc.invalidateQueries({ queryKey: ["me-overview"] });
    },
    onError: (err: Error) => message.error(err.message),
  });

  return (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 16,
        }}
      >
        <Title level={2} style={{ margin: 0 }}>
          {t.assets.title}
        </Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setOpen(true)}>
          {t.assets.add}
        </Button>
      </div>

      <Table
        loading={isLoading}
        dataSource={data?.items ?? []}
        rowKey="id"
        columns={[
          { title: "ID", dataIndex: "id", width: 70 },
          { title: t.common.name, dataIndex: "name" },
          {
            title: t.common.type,
            dataIndex: "asset_type",
            render: (v: string) => <Tag>{v}</Tag>,
            width: 150,
          },
          { title: t.assets.uri, dataIndex: "uri", ellipsis: true },
          { title: t.assets.env, dataIndex: "environment", width: 90 },
          {
            title: t.assets.owner,
            dataIndex: "owner",
            width: 220,
            render: (owner: string | null, record: Asset) => (
              <OwnerCell
                owner={owner}
                me={user?.email ?? null}
                onChange={(next) => updateOwner.mutate({ id: record.id, owner: next })}
                pending={updateOwner.isPending && updateOwner.variables?.id === record.id}
                locale={locale}
              />
            ),
          },
          {
            title: t.assets.openFindings,
            dataIndex: "open_findings_count",
            width: 130,
            render: (v: number) => (
              <Tag color={v > 0 ? "orange" : "green"}>{v}</Tag>
            ),
          },
        ]}
      />

      <Modal
        title={locale === "ko" ? "자산 추가" : "Add Asset"}
        open={open}
        onCancel={() => setOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={create.isPending}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{ owner: user?.email ?? "" }}
          onFinish={(values) => create.mutate(values)}
        >
          <Form.Item label={locale === "ko" ? "이름" : "Name"} name="name" rules={[{ required: true }]}>
            <Input placeholder="my-service" />
          </Form.Item>
          <Form.Item label={locale === "ko" ? "유형" : "Type"} name="asset_type" rules={[{ required: true }]}>
            <Select options={ASSET_TYPES.map((t) => ({ value: t, label: t }))} />
          </Form.Item>
          <Form.Item label="URI" name="uri" rules={[{ required: true }]}>
            <Input placeholder="https://github.com/org/repo 또는 docker://image:tag" />
          </Form.Item>
          <Form.Item
            label={locale === "ko" ? "담당자 (owner)" : "Owner"}
            name="owner"
            extra={
              locale === "ko"
                ? "기본값은 본인 이메일. 팀 alias나 다른 사람 이메일로 변경 가능. owner 자산은 My Mond에서 추적됩니다."
                : undefined
            }
          >
            <Input placeholder="alice@corp.com" />
          </Form.Item>
          <Form.Item label={locale === "ko" ? "환경" : "Environment"} name="environment">
            <Select
              allowClear
              options={["dev", "staging", "prod"].map((e) => ({ value: e, label: e }))}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

/** Owner inline 셀 — 미지정/타인/본인 3 상태 + 클릭 편집 + 1클릭 등록 */
function OwnerCell({
  owner,
  me,
  onChange,
  pending,
  locale,
}: {
  owner: string | null;
  me: string | null;
  onChange: (next: string | null) => void;
  pending: boolean;
  locale: "ko" | "en";
}) {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState(owner ?? "");
  const isMe = !!owner && !!me && owner === me;

  const editForm = (
    <Space direction="vertical" size={6} style={{ width: 240 }}>
      <Input
        size="small"
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        placeholder={me ?? "team-name"}
        onPressEnter={() => {
          onChange(draft.trim() || null);
          setOpen(false);
        }}
      />
      <Space size={4} wrap>
        <Button
          size="small"
          type="primary"
          onClick={() => {
            onChange(draft.trim() || null);
            setOpen(false);
          }}
        >
          {locale === "ko" ? "저장" : "Save"}
        </Button>
        {me && draft !== me && (
          <Button
            size="small"
            icon={<UserAddOutlined />}
            onClick={() => {
              setDraft(me);
              onChange(me);
              setOpen(false);
            }}
          >
            {locale === "ko" ? "나로" : "Me"}
          </Button>
        )}
        {owner && (
          <Button
            size="small"
            danger
            type="text"
            onClick={() => {
              onChange(null);
              setOpen(false);
            }}
          >
            {locale === "ko" ? "비우기" : "Clear"}
          </Button>
        )}
        <Button size="small" type="text" onClick={() => setOpen(false)}>
          {locale === "ko" ? "취소" : "Cancel"}
        </Button>
      </Space>
    </Space>
  );

  if (!owner) {
    return (
      <Space size={4}>
        <Tag color="default" style={{ marginInlineEnd: 0 }}>
          {locale === "ko" ? "담당자 미정" : "no owner"}
        </Tag>
        {me && (
          <Tooltip title={locale === "ko" ? `owner=${me} 로 등록` : `Set owner=${me}`}>
            <Button
              size="small"
              type="link"
              loading={pending}
              icon={<UserAddOutlined />}
              onClick={() => onChange(me)}
              style={{ paddingInline: 4, height: 22 }}
            >
              {locale === "ko" ? "내 자산으로" : "Take ownership"}
            </Button>
          </Tooltip>
        )}
      </Space>
    );
  }

  return (
    <Popover
      open={open}
      onOpenChange={(v) => {
        setOpen(v);
        if (v) setDraft(owner ?? "");
      }}
      trigger="click"
      content={editForm}
      destroyTooltipOnHide
    >
      <Space size={4} style={{ cursor: "pointer" }}>
        {isMe && <UserOutlined style={{ color: "var(--severity-info, #8a8aff)" }} />}
        <Text strong={isMe} style={{ color: isMe ? "var(--severity-info, #8a8aff)" : undefined }}>
          {owner}
        </Text>
        {isMe && (
          <Tag color="geekblue" style={{ marginInlineEnd: 0 }}>
            {locale === "ko" ? "내 자산" : "mine"}
          </Tag>
        )}
      </Space>
    </Popover>
  );
}
