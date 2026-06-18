/**
 * Scans — 스캔 이력 + 트리거
 */

import { ThunderboltOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Button,
  Form,
  Modal,
  Select,
  Table,
  Tag,
  Typography,
  message,
} from "antd";
import { useState } from "react";

import { useI18n } from "@/i18n";
import { api, type Asset, type Page, type Scan } from "@/lib/api";

const { Title } = Typography;

const SCANNERS = ["trivy", "semgrep", "nuclei"];

async function fetchScans(): Promise<Scan[]> {
  const { data } = await api.get<Scan[]>("/scans", { params: { limit: 100 } });
  return data;
}

async function fetchAssetsLite(): Promise<Asset[]> {
  const { data } = await api.get<Page<Asset>>("/assets", { params: { limit: 200 } });
  return data.items;
}

export default function Scans() {
  const { t } = useI18n();
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm();

  const { data, isLoading } = useQuery({
    queryKey: ["scans"],
    queryFn: fetchScans,
    refetchInterval: 5_000,
  });
  const { data: assets } = useQuery({ queryKey: ["assets-lite"], queryFn: fetchAssetsLite });

  const trigger = useMutation({
    mutationFn: (payload: { asset_id: number; scanner: string }) =>
      api.post<Scan>("/scans", { ...payload, trigger: "manual" }),
    onSuccess: () => {
      message.success("스캔이 실행되었습니다.");
      qc.invalidateQueries({ queryKey: ["scans"] });
      qc.invalidateQueries({ queryKey: ["findings"] });
      qc.invalidateQueries({ queryKey: ["dashboard-overview"] });
      setOpen(false);
      form.resetFields();
    },
    onError: (err) => message.error(`스캔 실패: ${err.message}`),
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
          {t.scans.title}
        </Title>
        <Button type="primary" icon={<ThunderboltOutlined />} onClick={() => setOpen(true)}>
          {t.scans.trigger}
        </Button>
      </div>

      <Table
        loading={isLoading}
        dataSource={data ?? []}
        rowKey="id"
        columns={[
          { title: "ID", dataIndex: "id", width: 70 },
          { title: t.common.asset, dataIndex: "asset_id", width: 110 },
          { title: t.common.scanner, dataIndex: "scanner", width: 140 },
          {
            title: t.common.status,
            dataIndex: "status",
            render: (s: string) => (
              <Tag color={s === "completed" ? "green" : s === "failed" ? "red" : "blue"}>
                {s}
              </Tag>
            ),
            width: 120,
          },
          {
            title: t.scans.trigger,
            dataIndex: "trigger",
            render: (v: string) => <Tag>{v}</Tag>,
            width: 110,
          },
          { title: t.scans.findingsCount, dataIndex: "findings_count", width: 110 },
          {
            title: t.scans.duration,
            dataIndex: "duration_ms",
            render: (v: number | null) => (v ? `${v} ms` : "—"),
            width: 110,
          },
          {
            title: t.common.when,
            dataIndex: "created_at",
            render: (v: string) => new Date(v).toLocaleString(),
          },
        ]}
      />

      <Modal
        title={t.scans.trigger}
        open={open}
        onCancel={() => setOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={trigger.isPending}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={(values) =>
            trigger.mutate({
              asset_id: values.asset_id,
              scanner: values.scanner,
            })
          }
        >
          <Form.Item label="Asset" name="asset_id" rules={[{ required: true }]}>
            <Select
              options={(assets ?? []).map((a) => ({
                value: a.id,
                label: `${a.name} (${a.asset_type})`,
              }))}
              showSearch
              optionFilterProp="label"
              placeholder="자산 선택"
            />
          </Form.Item>
          <Form.Item label="Scanner" name="scanner" rules={[{ required: true }]}>
            <Select options={SCANNERS.map((s) => ({ value: s, label: s }))} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
