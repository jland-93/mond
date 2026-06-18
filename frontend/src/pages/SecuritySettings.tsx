/**
 * 🌙 보안 설정 — 패스키 등록·삭제, TOTP setup/disable, 백업 코드
 */

import {
  DeleteOutlined,
  KeyOutlined,
  MobileOutlined,
  SafetyOutlined,
} from "@ant-design/icons";
import { startRegistration } from "@simplewebauthn/browser";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  Button,
  Card,
  Empty,
  Form,
  Input,
  List,
  Modal,
  Popconfirm,
  Space,
  Tag,
  Typography,
  message,
} from "antd";
import { useState } from "react";

import { useAuth } from "@/auth/AuthContext";
import { useI18n } from "@/i18n";
import { mfaApi } from "@/lib/mfa-api";

const { Title, Paragraph, Text } = Typography;

export default function SecuritySettings() {
  const { t, locale } = useI18n();
  const { refresh } = useAuth();
  const qc = useQueryClient();

  const { data: status, isLoading } = useQuery({
    queryKey: ["mfa-status"],
    queryFn: mfaApi.status,
  });

  const [passkeyName, setPasskeyName] = useState("");
  const [totpModal, setTotpModal] = useState<{
    open: boolean;
    qr?: string;
    secret?: string;
  }>({ open: false });
  const [totpCode, setTotpCode] = useState("");
  const [backupCodes, setBackupCodes] = useState<string[] | null>(null);

  const refreshAll = () => {
    qc.invalidateQueries({ queryKey: ["mfa-status"] });
    refresh();
  };

  // ── 패스키 등록 ───────────────────────────────
  const registerPasskey = useMutation({
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

  const deletePasskey = useMutation({
    mutationFn: (id: number) => mfaApi.passkeyDelete(id),
    onSuccess: () => {
      message.success(locale === "ko" ? "삭제됨" : "Deleted");
      refreshAll();
    },
  });

  // ── TOTP ───────────────────────────────────────
  const setupTotp = useMutation({
    mutationFn: () => mfaApi.totpSetup(),
    onSuccess: (data) => {
      setTotpModal({ open: true, qr: data.qr_png_base64, secret: data.secret });
    },
  });

  const verifyTotp = useMutation({
    mutationFn: (code: string) => mfaApi.totpVerify(code),
    onSuccess: () => {
      message.success(locale === "ko" ? "TOTP 등록 완료" : "TOTP enrolled");
      setTotpModal({ open: false });
      setTotpCode("");
      refreshAll();
    },
    onError: (e: Error & { response?: { data?: { detail?: string } } }) => {
      message.error(e.response?.data?.detail ?? e.message);
    },
  });

  const disableTotp = useMutation({
    mutationFn: () => mfaApi.totpDisable(),
    onSuccess: () => {
      message.success(locale === "ko" ? "TOTP 비활성화" : "TOTP disabled");
      refreshAll();
    },
  });

  // ── Backup codes ───────────────────────────────
  const regenBackup = useMutation({
    mutationFn: () => mfaApi.backupCodesRegenerate(),
    onSuccess: (data) => {
      setBackupCodes(data.codes);
      refreshAll();
    },
  });

  return (
    <div>
      <Title level={2} style={{ marginBottom: 4 }}>
        {t.security.title}
      </Title>
      <Paragraph type="secondary">{t.security.desc}</Paragraph>

      {status?.required && !status.enrolled && (
        <Alert
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
          message={t.security.requiredWarning}
        />
      )}

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
            loading={registerPasskey.isPending}
            onClick={() => registerPasskey.mutate()}
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
                    onConfirm={() => deletePasskey.mutate(p.id)}
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
              onConfirm={() => disableTotp.mutate()}
            >
              <Button danger>{t.security.disableTotp}</Button>
            </Popconfirm>
          ) : (
            <Button type="primary" onClick={() => setupTotp.mutate()} loading={setupTotp.isPending}>
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

      <Card
        title={
          <Space>
            <SafetyOutlined />
            <span>{t.security.backupCodes}</span>
          </Space>
        }
        extra={
          <Popconfirm
            title={t.security.confirmRegenBackup}
            onConfirm={() => regenBackup.mutate()}
          >
            <Button>{t.security.regenBackup}</Button>
          </Popconfirm>
        }
        loading={isLoading}
      >
        <Paragraph type="secondary">{t.security.backupCodesDesc}</Paragraph>
        <Tag color={status && status.backup_codes_remaining > 0 ? "green" : "default"}>
          {status?.backup_codes_remaining ?? 0} {t.security.remaining}
        </Tag>
      </Card>

      {/* TOTP setup 모달 */}
      <Modal
        open={totpModal.open}
        title={t.security.setupTotpTitle}
        onCancel={() => setTotpModal({ open: false })}
        onOk={() => verifyTotp.mutate(totpCode)}
        okText={t.security.verify}
        confirmLoading={verifyTotp.isPending}
        okButtonProps={{ disabled: !/^\d{6,8}$/.test(totpCode) }}
      >
        <Paragraph type="secondary">{t.security.setupTotpDesc}</Paragraph>
        {totpModal.qr && (
          <div style={{ textAlign: "center", margin: "12px 0" }}>
            <img
              src={`data:image/png;base64,${totpModal.qr}`}
              alt="TOTP QR"
              style={{ width: 200, height: 200, background: "#fff", padding: 8, borderRadius: 8 }}
            />
          </div>
        )}
        {totpModal.secret && (
          <Text type="secondary" copyable={{ text: totpModal.secret }} style={{ fontFamily: "monospace", fontSize: 12 }}>
            {t.security.totpSecret}: {totpModal.secret}
          </Text>
        )}
        <Form layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item label={t.security.enterTotpCode}>
            <Input
              autoFocus
              placeholder="123 456"
              value={totpCode}
              onChange={(e) => setTotpCode(e.target.value.replace(/\D/g, ""))}
              maxLength={8}
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* 백업 코드 1회 노출 모달 */}
      <Modal
        open={!!backupCodes}
        title={t.security.backupCodesTitle}
        onOk={() => setBackupCodes(null)}
        onCancel={() => setBackupCodes(null)}
        okText={t.security.savedIt}
        cancelButtonProps={{ style: { display: "none" } }}
      >
        <Alert
          showIcon
          type="warning"
          message={t.security.backupCodesWarn}
          style={{ marginBottom: 12 }}
        />
        <pre
          style={{
            background: "rgba(255,255,255,0.05)",
            padding: 12,
            borderRadius: 8,
            fontFamily: "monospace",
            fontSize: 13,
            lineHeight: 1.8,
            margin: 0,
          }}
        >
          {(backupCodes ?? []).join("\n")}
        </pre>
      </Modal>
    </div>
  );
}
