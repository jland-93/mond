/**
 * AI Providers 등록·전환 카드 — Anthropic / OpenAI / Bedrock / Ollama 4종.
 * 키는 SECRET_KEY로 암호화돼 DB 저장. UI에는 마스킹된 값만.
 */

import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  DeleteOutlined,
  PlusOutlined,
  RobotOutlined,
  ThunderboltOutlined,
} from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Button,
  Card,
  Col,
  Form,
  Input,
  Modal,
  Popconfirm,
  Row,
  Space,
  Tag,
  Typography,
  message,
} from "antd";
import { useState } from "react";

import { useI18n } from "@/i18n";
import {
  aiProvidersApi,
  type AIProviderName,
  type AIProviderUpsert,
} from "@/lib/ai-providers-api";

import { AI_PROVIDERS } from "./constants";

const { Paragraph } = Typography;

export default function AIProvidersCard() {
  const { t, locale } = useI18n();
  const qc = useQueryClient();
  const { data: rows } = useQuery({ queryKey: ["ai-providers"], queryFn: aiProvidersApi.list });
  const [openProvider, setOpenProvider] = useState<AIProviderName | null>(null);
  const [form] = Form.useForm();

  const byName = (n: AIProviderName) => (rows ?? []).find((r) => r.provider === n);
  const defaultRow = (rows ?? []).find((r) => r.is_default && r.enabled);

  const save = useMutation({
    mutationFn: (body: AIProviderUpsert) => aiProvidersApi.upsert(body),
    onSuccess: () => {
      message.success(locale === "ko" ? "저장됨" : "Saved");
      qc.invalidateQueries({ queryKey: ["ai-providers"] });
      qc.invalidateQueries({ queryKey: ["ai-status"] });
      setOpenProvider(null);
      form.resetFields();
    },
    onError: (e: Error & { response?: { data?: { detail?: string } } }) => {
      message.error(e.response?.data?.detail ?? e.message);
    },
  });

  const activate = useMutation({
    mutationFn: (id: number) => aiProvidersApi.activate(id),
    onSuccess: () => {
      message.success(locale === "ko" ? "활성 provider 변경됨" : "Active provider switched");
      qc.invalidateQueries({ queryKey: ["ai-providers"] });
      qc.invalidateQueries({ queryKey: ["ai-status"] });
    },
  });

  const remove = useMutation({
    mutationFn: (id: number) => aiProvidersApi.remove(id),
    onSuccess: () => {
      message.success(locale === "ko" ? "삭제됨" : "Deleted");
      qc.invalidateQueries({ queryKey: ["ai-providers"] });
      qc.invalidateQueries({ queryKey: ["ai-status"] });
    },
  });

  const testConn = useMutation({
    mutationFn: (body: AIProviderUpsert) => aiProvidersApi.test(body),
    onSuccess: (r) => {
      if (r.ok) message.success(`${r.provider}:${r.model} OK`);
      else message.error(`연결 실패: ${r.detail}`);
    },
  });

  return (
    <Card
      title={
        <Space>
          <RobotOutlined />
          <span>{locale === "ko" ? "AI Providers" : "AI Providers"}</span>
          {defaultRow && (
            <Tag color="green">
              {locale === "ko" ? "활성" : "Active"} · {defaultRow.provider}
            </Tag>
          )}
        </Space>
      }
      style={{ marginBottom: 16 }}
    >
      <Paragraph type="secondary">
        {locale === "ko"
          ? "관리자가 직접 AI API key를 등록하면 .env 수정·재시작 없이 즉시 반영됩니다. key는 SECRET_KEY로 암호화돼 저장되고, UI에는 마스킹된 값만 표시됩니다."
          : "Register AI keys here for instant effect — no .env edit or restart. Keys are encrypted with SECRET_KEY; only masked values are shown."}
      </Paragraph>
      <Row gutter={[12, 12]}>
        {AI_PROVIDERS.map((p) => {
          const row = byName(p.name);
          const ready = row?.enabled && (row.has_api_key || !p.needsKey || row.base_url || row.region);
          return (
            <Col xs={24} md={12} key={p.name}>
              <Card type="inner" size="small" title={p.label}>
                <Space direction="vertical" style={{ width: "100%" }}>
                  <Space wrap>
                    {row?.is_default && row?.enabled && (
                      <Tag color="green" icon={<CheckCircleOutlined />}>
                        {locale === "ko" ? "활성" : "Active"}
                      </Tag>
                    )}
                    {row && !row.enabled && (
                      <Tag color="default" icon={<CloseCircleOutlined />}>
                        {locale === "ko" ? "비활성" : "Disabled"}
                      </Tag>
                    )}
                    {row?.has_api_key && (
                      <Tag>
                        key: <code style={{ fontFamily: "monospace" }}>{row.api_key_masked}</code>
                      </Tag>
                    )}
                    {row?.model_default && <Tag>{row.model_default}</Tag>}
                    {row?.base_url && <Tag>{row.base_url}</Tag>}
                    {row?.region && <Tag>{row.region}</Tag>}
                    {!row && (
                      <Tag color="default">
                        {locale === "ko" ? "미등록 — ENV fallback 사용" : "Not configured — ENV fallback"}
                      </Tag>
                    )}
                  </Space>
                  <Space>
                    <Button
                      type="primary"
                      icon={<PlusOutlined />}
                      onClick={() => {
                        setOpenProvider(p.name);
                        form.setFieldsValue({
                          provider: p.name,
                          enabled: row?.enabled ?? true,
                          is_default: row?.is_default ?? !defaultRow,
                          base_url: row?.base_url ?? "",
                          region: row?.region ?? "",
                          model_default: row?.model_default ?? "",
                          model_deep: row?.model_deep ?? "",
                          api_key: "",
                        });
                      }}
                    >
                      {row ? (locale === "ko" ? "수정" : "Edit") : (locale === "ko" ? "등록" : "Set up")}
                    </Button>
                    {row && !row.is_default && ready && (
                      <Button icon={<ThunderboltOutlined />} onClick={() => activate.mutate(row.id)}>
                        {locale === "ko" ? "활성화" : "Activate"}
                      </Button>
                    )}
                    {row && (
                      <Popconfirm
                        title={locale === "ko" ? "이 provider 설정을 삭제할까요?" : "Delete this provider config?"}
                        okType="danger"
                        onConfirm={() => remove.mutate(row.id)}
                      >
                        <Button danger icon={<DeleteOutlined />}>
                          {locale === "ko" ? "삭제" : "Remove"}
                        </Button>
                      </Popconfirm>
                    )}
                  </Space>
                </Space>
              </Card>
            </Col>
          );
        })}
      </Row>

      <Modal
        title={
          <Space>
            <RobotOutlined />
            <span>
              {locale === "ko" ? "AI Provider 등록" : "Configure AI Provider"} —{" "}
              {AI_PROVIDERS.find((p) => p.name === openProvider)?.label}
            </span>
          </Space>
        }
        open={!!openProvider}
        onCancel={() => {
          setOpenProvider(null);
          form.resetFields();
        }}
        onOk={() => form.submit()}
        okText={locale === "ko" ? "저장" : "Save"}
        confirmLoading={save.isPending}
        width={620}
        footer={[
          <Button key="cancel" onClick={() => setOpenProvider(null)}>
            {t.common.cancel ?? (locale === "ko" ? "취소" : "Cancel")}
          </Button>,
          <Button
            key="test"
            icon={<ThunderboltOutlined />}
            loading={testConn.isPending}
            onClick={() => {
              const v = form.getFieldsValue();
              testConn.mutate({
                provider: v.provider,
                api_key: v.api_key || undefined,
                base_url: v.base_url || undefined,
                region: v.region || undefined,
                model_default: v.model_default || undefined,
              });
            }}
          >
            {locale === "ko" ? "테스트 연결" : "Test connection"}
          </Button>,
          <Button key="save" type="primary" loading={save.isPending} onClick={() => form.submit()}>
            {locale === "ko" ? "저장" : "Save"}
          </Button>,
        ]}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={(v: Record<string, string | boolean>) => save.mutate(v as unknown as AIProviderUpsert)}
        >
          <Form.Item name="provider" hidden>
            <Input />
          </Form.Item>

          {openProvider && AI_PROVIDERS.find((p) => p.name === openProvider)?.needsKey && (
            <Form.Item
              label={locale === "ko" ? "API Key (비워두면 기존 값 유지)" : "API Key (leave empty to keep current)"}
              name="api_key"
              extra={
                locale === "ko"
                  ? "저장 시 SECRET_KEY로 암호화돼 DB에 저장됩니다. 다시 표시되지 않습니다."
                  : "Encrypted with SECRET_KEY when saved. Not shown again."
              }
            >
              <Input.Password placeholder={AI_PROVIDERS.find((p) => p.name === openProvider)?.placeholder} />
            </Form.Item>
          )}

          {openProvider === "openai" && (
            <Form.Item
              label={locale === "ko" ? "base_url (선택 — Azure / 사내 게이트웨이)" : "base_url (optional — Azure / gateway)"}
              name="base_url"
            >
              <Input placeholder="https://your-azure.openai.azure.com/" />
            </Form.Item>
          )}

          {openProvider === "ollama" && (
            <Form.Item
              label={locale === "ko" ? "base_url" : "base_url"}
              name="base_url"
              rules={[{ required: true }]}
            >
              <Input placeholder="http://ollama.internal:11434" />
            </Form.Item>
          )}

          {openProvider === "bedrock" && (
            <Form.Item label="region" name="region" rules={[{ required: true }]}>
              <Input placeholder="us-east-1 / ap-northeast-2" />
            </Form.Item>
          )}

          <Space style={{ width: "100%" }} size="middle">
            <Form.Item label="model_default" name="model_default" style={{ width: 280 }}>
              <Input placeholder="claude-haiku-4-5-... / gpt-4o-mini / llama3.1:8b" />
            </Form.Item>
            <Form.Item label="model_deep" name="model_deep" style={{ width: 280 }}>
              <Input placeholder="claude-sonnet-4-6 / gpt-4o / llama3.1:70b" />
            </Form.Item>
          </Space>

          <Space size="large">
            <Form.Item
              name="enabled"
              valuePropName="checked"
              label={locale === "ko" ? "활성화" : "Enabled"}
            >
              <input type="checkbox" />
            </Form.Item>
            <Form.Item
              name="is_default"
              valuePropName="checked"
              label={locale === "ko" ? "기본 provider로 설정" : "Set as default"}
              tooltip={
                locale === "ko"
                  ? "기본 provider는 시스템 전체가 1개만 가질 수 있습니다."
                  : "Only one provider can be the default at a time."
              }
            >
              <input type="checkbox" />
            </Form.Item>
          </Space>
        </Form>
      </Modal>
    </Card>
  );
}
