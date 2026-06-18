/**
 * TOTP (Time-based OTP) setup · verify · disable.
 */

import { MobileOutlined, SafetyOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button, Card, Form, Input, Modal, Popconfirm, Space, Tag, Typography, message } from "antd";
import { useState } from "react";

import { useAuth } from "@/auth/AuthContext";
import { useI18n } from "@/i18n";
import { mfaApi } from "@/lib/mfa-api";

const { Paragraph, Text } = Typography;

export default function TOTPCard() {
  const { t, locale } = useI18n();
  const { refresh } = useAuth();
  const qc = useQueryClient();

  const { data: status, isLoading } = useQuery({
    queryKey: ["mfa-status"],
    queryFn: mfaApi.status,
  });

  const [modal, setModal] = useState<{ open: boolean; qr?: string; secret?: string }>({ open: false });
  const [code, setCode] = useState("");

  const refreshAll = () => {
    qc.invalidateQueries({ queryKey: ["mfa-status"] });
    refresh();
  };

  const setup = useMutation({
    mutationFn: () => mfaApi.totpSetup(),
    onSuccess: (data) => {
      setModal({ open: true, qr: data.qr_png_base64, secret: data.secret });
    },
  });

  const verify = useMutation({
    mutationFn: (c: string) => mfaApi.totpVerify(c),
    onSuccess: () => {
      message.success(locale === "ko" ? "TOTP 등록 완료" : "TOTP enrolled");
      setModal({ open: false });
      setCode("");
      refreshAll();
    },
    onError: (e: Error & { response?: { data?: { detail?: string } } }) => {
      message.error(e.response?.data?.detail ?? e.message);
    },
  });

  const disable = useMutation({
    mutationFn: () => mfaApi.totpDisable(),
    onSuccess: () => {
      message.success(locale === "ko" ? "TOTP 비활성화" : "TOTP disabled");
      refreshAll();
    },
  });

  return (
    <>
      <Card
        title={
          <Space>
            <MobileOutlined />
            <span>{t.security.totp}</span>
          </Space>
        }
        extra={
          status?.totp_confirmed ? (
            <Popconfirm
              title={t.security.confirmDisableTotp}
              okType="danger"
              onConfirm={() => disable.mutate()}
            >
              <Button danger>{t.security.disableTotp}</Button>
            </Popconfirm>
          ) : (
            <Button type="primary" onClick={() => setup.mutate()} loading={setup.isPending}>
              {t.security.setupTotp}
            </Button>
          )
        }
        style={{ marginBottom: 16 }}
        loading={isLoading}
      >
        <Paragraph type="secondary">{t.security.totpDesc}</Paragraph>
        {status?.totp_confirmed && (
          <Tag color="green" icon={<SafetyOutlined />}>
            {t.security.enabled}
          </Tag>
        )}
      </Card>

      <Modal
        open={modal.open}
        title={t.security.setupTotpTitle}
        onCancel={() => setModal({ open: false })}
        onOk={() => verify.mutate(code)}
        okText={t.security.verify}
        confirmLoading={verify.isPending}
        okButtonProps={{ disabled: !/^\d{6,8}$/.test(code) }}
      >
        <Paragraph type="secondary">{t.security.setupTotpDesc}</Paragraph>
        {modal.qr && (
          <div style={{ textAlign: "center", margin: "12px 0" }}>
            <img
              src={`data:image/png;base64,${modal.qr}`}
              alt="TOTP QR"
              style={{ width: 200, height: 200, background: "#fff", padding: 8, borderRadius: 8 }}
            />
          </div>
        )}
        {modal.secret && (
          <Text type="secondary" copyable={{ text: modal.secret }} style={{ fontFamily: "monospace", fontSize: 12 }}>
            {t.security.totpSecret}: {modal.secret}
          </Text>
        )}
        <Form layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item label={t.security.enterTotpCode}>
            <Input
              autoFocus
              placeholder="123 456"
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
              maxLength={8}
            />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
