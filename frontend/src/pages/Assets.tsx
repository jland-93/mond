/**
 * 🌙 Assets — 자산 인벤토리
 */

import { PlusOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Button,
  Form,
  Input,
  Modal,
  Select,
  Table,
  Tag,
  Typography,
  message,
} from "antd";
import { useState } from "react";

import { useI18n } from "@/i18n";
import { api, type Asset, type AssetType, type Page } from "@/lib/api";

const { Title } = Typography;

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
  const { t } = useI18n();
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
      message.success("자산이 추가되었습니다.");
      qc.invalidateQueries({ queryKey: ["assets"] });
      setOpen(false);
      form.resetFields();
    },
    onError: (err) => message.error(`추가 실패: ${err.message}`),
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
          { title: "Name", dataIndex: "name" },
          {
            title: "Type",
            dataIndex: "asset_type",
            render: (t: string) => <Tag>{t}</Tag>,
            width: 150,
          },
          { title: "URI", dataIndex: "uri", ellipsis: true },
          { title: "Env", dataIndex: "environment", width: 90 },
          { title: "Owner", dataIndex: "owner", width: 120 },
          {
            title: "Open Findings",
            dataIndex: "open_findings_count",
            width: 130,
            render: (v: number) => (
              <Tag color={v > 0 ? "orange" : "green"}>{v}</Tag>
            ),
          },
        ]}
      />

      <Modal
        title="Add Asset"
        open={open}
        onCancel={() => setOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={create.isPending}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={(values) => create.mutate(values)}
        >
          <Form.Item label="Name" name="name" rules={[{ required: true }]}>
            <Input placeholder="my-service" />
          </Form.Item>
          <Form.Item label="Type" name="asset_type" rules={[{ required: true }]}>
            <Select options={ASSET_TYPES.map((t) => ({ value: t, label: t }))} />
          </Form.Item>
          <Form.Item label="URI" name="uri" rules={[{ required: true }]}>
            <Input placeholder="https://github.com/org/repo 또는 docker://image:tag" />
          </Form.Item>
          <Form.Item label="Owner" name="owner">
            <Input placeholder="team-name" />
          </Form.Item>
          <Form.Item label="Environment" name="environment">
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
