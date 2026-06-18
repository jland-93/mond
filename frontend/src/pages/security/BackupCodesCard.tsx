/**
 * Backup codes — 1회용 코드 10개. 재생성 시 평문은 단 한 번만 노출.
 */

import { SafetyOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, Button, Card, Modal, Popconfirm, Space, Tag, Typography } from "antd";
import { useState } from "react";

import { useAuth } from "@/auth/AuthContext";
import { useI18n } from "@/i18n";
import { mfaApi } from "@/lib/mfa-api";

const { Paragraph } = Typography;

export default function BackupCodesCard() {
  const { t, locale } = useI18n();
  const { refresh } = useAuth();
  const qc = useQueryClient();
  const [codes, setCodes] = useState<string[] | null>(null);

  const { data: status, isLoading } = useQuery({
    queryKey: ["mfa-status"],
    queryFn: mfaApi.status,
  });

  const regen = useMutation({
    mutationFn: () => mfaApi.backupCodesRegenerate(),
    onSuccess: (data) => {
      setCodes(data.codes);
      qc.invalidateQueries({ queryKey: ["mfa-status"] });
      refresh();
    },
  });

  return (
    <>
      <Card
        title={
          <Space>
            <SafetyOutlined />
            <span>{t.security.backupCodes}</span>
          </Space>
        }
        extra={
          <Popconfirm title={t.security.confirmRegenBackup} onConfirm={() => regen.mutate()}>
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

      <Modal
        open={!!codes}
        title={t.security.backupCodesTitle}
        onOk={() => setCodes(null)}
        onCancel={() => setCodes(null)}
        okText={t.security.savedIt}
        cancelButtonProps={{ style: { display: "none" } }}
      >
        <Alert showIcon type="warning" message={t.security.backupCodesWarn} style={{ marginBottom: 12 }} />
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
          {(codes ?? []).join("\n")}
        </pre>
      </Modal>
    </>
  );
}
