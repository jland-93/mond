/**
 * Scans — 스캔 이력 + 트리거
 */

import { RobotOutlined, ThunderboltOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Button,
  Form,
  Modal,
  Select,
  Space,
  Table,
  Tag,
  Tooltip,
  Typography,
  message,
} from "antd";
import { useState } from "react";

import { useI18n } from "@/i18n";
import { api, type Asset, type Page, type Scan } from "@/lib/api";

const { Title, Text } = Typography;

const SCANNERS = ["trivy", "semgrep", "nuclei"];

const TRIGGER_COLOR: Record<string, string> = {
  manual: "default",
  scheduled: "blue",
  webhook: "purple",
  ai: "magenta",
};

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
        expandable={{
          rowExpandable: (r) => !!r.router_decision || !!r.error_message,
          expandedRowRender: (r) => (
            <Space direction="vertical" size={6} style={{ paddingBlock: 4 }}>
              {r.router_decision && (
                <Space size={6} wrap>
                  <Tag color="purple" icon={<RobotOutlined />}>
                    auto-router
                  </Tag>
                  <Text>{r.router_decision.reason}</Text>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    SAST {r.router_decision.counts.sast} · SCA {r.router_decision.counts.sca} ·
                    Container {r.router_decision.counts.container} · IaC {r.router_decision.counts.iac} ·
                    기타 {r.router_decision.counts.unknown}
                  </Text>
                  {r.router_decision.fallback && (
                    <Tag color="default" style={{ fontSize: 11 }}>
                      fallback
                    </Tag>
                  )}
                </Space>
              )}
              {r.error_message && (
                <Text type="danger" style={{ fontSize: 12 }}>
                  {r.error_message}
                </Text>
              )}
            </Space>
          ),
        }}
        columns={[
          { title: "ID", dataIndex: "id", width: 70 },
          {
            title: t.common.asset,
            dataIndex: "asset_name",
            render: (name: string | null | undefined, r: Scan) => (
              <Tooltip title={`asset_id=${r.asset_id}`}>
                <Text>{name || `#${r.asset_id}`}</Text>
              </Tooltip>
            ),
          },
          { title: t.common.scanner, dataIndex: "scanner", width: 120 },
          {
            title: t.common.status,
            dataIndex: "status",
            render: (s: string) => (
              <Tag color={s === "completed" ? "green" : s === "failed" ? "red" : "blue"}>
                {s}
              </Tag>
            ),
            width: 110,
          },
          {
            title: t.scans.trigger,
            dataIndex: "trigger",
            render: (v: string, r: Scan) => (
              <Space size={4}>
                <Tag color={TRIGGER_COLOR[v] ?? "default"} style={{ marginInlineEnd: 0 }}>
                  {v}
                </Tag>
                {r.router_decision && (
                  <Tooltip title={r.router_decision.reason}>
                    <Tag color="purple" style={{ marginInlineEnd: 0 }} icon={<RobotOutlined />}>
                      auto
                    </Tag>
                  </Tooltip>
                )}
              </Space>
            ),
            width: 150,
          },
          { title: t.scans.findingsCount, dataIndex: "findings_count", width: 100 },
          {
            title: t.scans.duration,
            dataIndex: "duration_ms",
            render: (v: number | null) => (v ? `${v} ms` : "—"),
            width: 100,
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
