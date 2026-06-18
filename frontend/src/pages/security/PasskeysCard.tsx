/**
 * 패스키(WebAuthn / FIDO2) 등록 · 목록 · 삭제.
 */

import { DeleteOutlined, KeyOutlined } from "@ant-design/icons";
import { startRegistration } from "@simplewebauthn/browser";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button, Card, Empty, Input, List, Popconfirm, Space, Tag, Typography, message } from "antd";
import { useState } from "react";

import { useAuth } from "@/auth/AuthContext";
import { useI18n } from "@/i18n";
import { mfaApi } from "@/lib/mfa-api";

const { Paragraph, Text } = Typography;

export default function PasskeysCard() {
  const { t, locale } = useI18n();
  const { refresh } = useAuth();
  const qc = useQueryClient();
  const [passkeyName, setPasskeyName] = useState("");

  const { data: status, isLoading } = useQuery({
    queryKey: ["mfa-status"],
    queryFn: mfaApi.status,
  });

  const refreshAll = () => {
    qc.invalidateQueries({ queryKey: ["mfa-status"] });
    refresh();
  };

  const register = useMutation({
    mutationFn: async () => {
      const name = passkeyName.trim() || (locale === "ko" ? "패스키" : "Passkey");
      const options = await mfaApi.passkeyRegisterBegin();
      const credential = await startRegistration({ optionsJSON: options as never });
      return mfaApi.passkeyRegisterComplete(name, credential as unknown as Record<string, unknown>);
    },
    onSuccess: (cred) => {
      message.success(`${cred.name} ${locale === "ko" ? "등록됨" : "registered"}`);
      setPasskeyName("");
      refreshAll();
    },
    onError: (e: Error & { response?: { data?: { detail?: string } } }) => {
      message.error(e.response?.data?.detail ?? e.message);
    },
  });

  const remove = useMutation({
    mutationFn: (id: number) => mfaApi.passkeyDelete(id),
    onSuccess: () => {
      message.success(locale === "ko" ? "삭제됨" : "Deleted");
      refreshAll();
    },
  });

  return (
    <Card
      title={
        <Space>
          <KeyOutlined />
          <span>{t.security.passkeys}</span>
        </Space>
      }
      style={{ marginBottom: 16 }}
      loading={isLoading}
    >
      <Paragraph type="secondary" style={{ marginBottom: 12 }}>
        {t.security.passkeysDesc}
      </Paragraph>
      <Space.Compact style={{ marginBottom: 12, width: "100%", maxWidth: 520 }}>
        <Input
          placeholder={t.security.passkeyNameHint}
          value={passkeyName}
          onChange={(e) => setPasskeyName(e.target.value)}
        />
        <Button
          type="primary"
          icon={<KeyOutlined />}
          loading={register.isPending}
          onClick={() => register.mutate()}
        >
          {t.security.addPasskey}
        </Button>
      </Space.Compact>

      {(status?.passkeys.length ?? 0) === 0 ? (
        <Empty description={t.security.noPasskeys} />
      ) : (
        <List
          dataSource={status?.passkeys ?? []}
          renderItem={(p) => (
            <List.Item
              actions={[
                <Popconfirm
                  key="del"
                  title={t.security.confirmDeletePasskey}
                  okType="danger"
                  onConfirm={() => remove.mutate(p.id)}
                >
                  <Button type="text" danger icon={<DeleteOutlined />} />
                </Popconfirm>,
              ]}
            >
              <List.Item.Meta
                title={
                  <Space>
                    <Text strong>{p.name}</Text>
                    {(p.transports ?? []).filter(Boolean).map((tr) => (
                      <Tag key={tr}>{tr}</Tag>
                    ))}
                  </Space>
                }
                description={
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {p.created_at?.slice(0, 19).replace("T", " ")}
                    {p.last_used_at &&
                      ` · ${t.security.lastUsed} ${p.last_used_at.slice(0, 19).replace("T", " ")}`}
                  </Text>
                }
              />
            </List.Item>
          )}
        />
      )}
    </Card>
  );
}
