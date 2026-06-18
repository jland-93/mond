/**
 * Admin · Connections 공통 상수 — IAM source 타입 라벨 / capability status 표기 / AI provider 메타.
 */

import type { IAMCapability, IAMSourceKind } from "@/lib/iam-api";
import type { AIProviderName } from "@/lib/ai-providers-api";

export const KIND_LABEL: Record<IAMSourceKind, string> = {
  aws: "AWS",
  k8s: "Kubernetes",
  ldap: "LDAP / Active Directory (온프레미스)",
  gcp: "Google Cloud",
  azure: "Azure",
  custom: "Custom Webhook",
};

export const STATUS_COLOR: Record<IAMCapability["status"], string> = {
  ready: "green",
  demo: "orange",
  coming_soon: "default",
};

export const STATUS_LABEL_KO: Record<IAMCapability["status"], string> = {
  ready: "정상 동작",
  demo: "데모 데이터만",
  coming_soon: "곧 지원",
};

export const STATUS_LABEL_EN: Record<IAMCapability["status"], string> = {
  ready: "Ready",
  demo: "Demo only",
  coming_soon: "Coming soon",
};

export const AI_PROVIDERS: {
  name: AIProviderName;
  label: string;
  needsKey: boolean;
  placeholder: string;
}[] = [
  { name: "anthropic", label: "Anthropic Claude", needsKey: true, placeholder: "sk-ant-..." },
  { name: "openai", label: "OpenAI / Azure OpenAI", needsKey: true, placeholder: "sk-proj-..." },
  { name: "bedrock", label: "AWS Bedrock (IAM 자격)", needsKey: false, placeholder: "(boto3가 IAM 자격 자동 감지)" },
  { name: "ollama", label: "Ollama / vLLM (로컬)", needsKey: false, placeholder: "(base_url로 호출)" },
];
