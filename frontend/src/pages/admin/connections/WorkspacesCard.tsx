/**
 * Workspace CRUD — 다중 조직/팀이 한 Mond 인스턴스를 공유할 때 자산 scope.
 *
 * v0.3 MVP는 Asset만 workspace로 분리한다. Policy/Finding/IAM 등 나머지 자원은
 * NULL이면 모든 workspace에서 visible — 단일 조직 운영에 영향 0.
 */

import { DeleteOutlined, PlusOutlined, StarFilled, StarOutlined, TeamOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  Button,
  Card,
  Form,
  Input,
  Modal,
  Popconfirm,
  Space,
  Table,
  Tag,
  Tooltip,
  Typography,
  message,
} from "antd";
import { useState } from "react";

import { useI18n } from "@/i18n";
import { api } from "@/lib/api";

const { Paragraph, Text } = Typography;

interface Workspace {
  id: number;
  slug: string;
  name: string;
  description: string | null;
  is_default: boolean;
}

export default function WorkspacesCard() {
  const { locale } = useI18n();
  const qc = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm();

  const { data: rows, isLoading } = useQuery({
    queryKey: ["admin-workspaces"],
    queryFn: async () => (await api.get<Workspace[]>("/admin/workspaces")).data,
  });

  const invalidate = () => qc.invalidateQueries({ queryKey: ["admin-workspaces"] });

  const create = useMutation({
    mutationFn: async (values: { slug: string; name: string; description?: string }) =>
      (await api.post<Workspace>("/admin/workspaces", values)).data,
    onSuccess: () => {
      message.success(locale === "ko" ? "워크스페이스 추가 완료" : "Workspace created");
      setModalOpen(false);
      form.resetFields();
      invalidate();
    },
    onError: (e: Error & { response?: { data?: { detail?: string } } }) =>
      message.error(e.response?.data?.detail ?? e.message),
  });

  const setDefault = useMutation({
    mutationFn: async (id: number) => (await api.post(`/admin/workspaces/${id}/default`)).data,
    onSuccess: () => {
      message.success(locale === "ko" ? "기본 워크스페이스 변경됨" : "Default updated");
      invalidate();
    },
  });

  const remove = useMutation({
    mutationFn: async (id: number) => api.delete(`/admin/workspaces/${id}`),
    onSuccess: () => {
      message.success(locale === "ko" ? "워크스페이스 삭제됨" : "Workspace deleted");
      invalidate();
    },
    onError: (e: Error & { response?: { data?: { detail?: string } } }) =>
      message.error(e.response?.data?.detail ?? e.message),
  });

  return (
    <Card
      title={
        <Space>
          <TeamOutlined />
          <span>{locale === "ko" ? "워크스페이스" : "Workspaces"}</span>
          <Tag>v0.3 MVP — Asset only</Tag>
        </Space>
      }
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
          {locale === "ko" ? "추가" : "Add"}
        </Button>
      }
      style={{ marginBottom: 16 }}
    >
      <Paragraph type="secondary" style={{ marginBottom: 12 }}>
        {locale === "ko"
          ? "여러 팀/조직이 한 Mond 인스턴스를 공유할 때 자산을 분리합니다. v0.3에서는 Asset만 workspace로 분리되고, workspace_id가 비어 있으면(NULL) 모든 workspace에서 보입니다. Policy/Finding/IAM 등 나머지 자원은 v0.4에서 확장됩니다."
          : "Scope assets when multiple teams share one Mond instance. v0.3 covers Asset only; null workspace_id means visible across all workspaces. Policies/findings/IAM coverage in v0.4."}
      </Paragraph>

      <Table
        size="small"
        rowKey="id"
        loading={isLoading}
        dataSource={rows ?? []}
        pagination={false}
        columns={[
          {
            title: locale === "ko" ? "기본" : "Default",
            dataIndex: "is_default",
            width: 70,
            render: (v: boolean, r: Workspace) =>
              v ? (
                <Tooltip title={locale === "ko" ? "기본 워크스페이스" : "Default"}>
                  <StarFilled style={{ color: "#faad14" }} />
                </Tooltip>
              ) : (
                <Tooltip title={locale === "ko" ? "기본으로 설정" : "Set as default"}>
                  <Button
                    type="text"
                    size="small"
                    icon={<StarOutlined />}
                    onClick={() => setDefault.mutate(r.id)}
                  />
                </Tooltip>
              ),
          },
          { title: "Slug", dataIndex: "slug", width: 160, render: (s: string) => <code>{s}</code> },
          { title: locale === "ko" ? "이름" : "Name", dataIndex: "name" },
          {
            title: locale === "ko" ? "설명" : "Description",
            dataIndex: "description",
            render: (v: string | null) => v ?? <Text type="secondary">—</Text>,
          },
          {
            title: "",
            width: 70,
            render: (_: unknown, r: Workspace) => (
              <Popconfirm
                title={
                  locale === "ko"
                    ? "이 워크스페이스를 삭제할까요? 자산의 workspace_id는 NULL로 풀립니다."
                    : "Delete this workspace? Asset.workspace_id will be set to NULL."
                }
                onConfirm={() => remove.mutate(r.id)}
                disabled={r.is_default}
              >
                <Tooltip
                  title={
                    r.is_default
                      ? locale === "ko"
                        ? "기본 워크스페이스는 삭제 불가"
                        : "Cannot delete default"
                      : ""
                  }
                >
                  <Button danger type="text" icon={<DeleteOutlined />} disabled={r.is_default} />
                </Tooltip>
              </Popconfirm>
            ),
          },
        ]}
      />

      <Alert
        type="info"
        showIcon
        style={{ marginTop: 12 }}
        message={
          locale === "ko"
            ? "API: GET/POST/PATCH/DELETE /api/v1/admin/workspaces, POST .../{id}/default. Asset 목록 조회 시 ?workspace_id=N을 붙이면 해당 ws + 미배정(NULL) 자산만 반환."
            : "API: GET/POST/PATCH/DELETE /api/v1/admin/workspaces, POST .../{id}/default. Asset list with ?workspace_id=N returns that ws + unscoped (NULL) assets."
        }
      />

      <Modal
        title={locale === "ko" ? "워크스페이스 추가" : "Add workspace"}
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={create.isPending}
      >
        <Form form={form} layout="vertical" onFinish={(values) => create.mutate(values)}>
          <Form.Item
            name="slug"
            label="Slug"
            rules={[
              { required: true },
              {
                pattern: /^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$/,
                message:
                  locale === "ko"
                    ? "소문자/숫자/하이픈, 시작·끝은 영숫자, 1~64자"
                    : "lowercase + digits + hyphen, alphanumeric at ends, 1-64",
              },
            ]}
            extra={locale === "ko" ? "URL/헤더 식별자. 예: platform, mobile-team" : "URL/header identifier"}
          >
            <Input placeholder="e.g. platform" />
          </Form.Item>
          <Form.Item
            name="name"
            label={locale === "ko" ? "이름" : "Name"}
            rules={[{ required: true, max: 128 }]}
          >
            <Input placeholder={locale === "ko" ? "예: Platform 팀" : "e.g. Platform Team"} />
          </Form.Item>
          <Form.Item
            name="description"
            label={locale === "ko" ? "설명 (선택)" : "Description (optional)"}
            rules={[{ max: 512 }]}
          >
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
}
