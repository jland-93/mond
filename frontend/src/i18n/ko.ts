/**
 * 🌙 Mond — 한국어 사전 (기본)
 */
export const ko = {
  appTagline: "AI 기반 셀프서비스 DevSecOps 플랫폼",
  language: { ko: "한국어", en: "English" },

  menu: {
    dashboard: "대시보드",
    assets: "자산",
    scans: "스캔",
    findings: "발견사항",
    policies: "정책",
    policySim: "정책 시뮬레이션",
    aiInsights: "AI 인사이트",
    regulations: "규제 가이드",
    reports: "리포트",
    integrations: "통합",
    settings: "설정",
  },

  common: {
    add: "추가",
    cancel: "취소",
    confirm: "확인",
    save: "저장",
    delete: "삭제",
    edit: "수정",
    refresh: "새로고침",
    download: "다운로드",
    runScan: "스캔 실행",
    runTriage: "AI Triage 실행",
    severity: "심각도",
    status: "상태",
    title: "제목",
    name: "이름",
    type: "유형",
    when: "시각",
    scanner: "스캐너",
    asset: "자산",
    description: "설명",
    enabled: "활성",
    disabled: "비활성",
    none: "없음",
    yes: "예",
    no: "아니오",
  },

  dashboard: {
    title: "대시보드",
    securityScore: "보안 점수",
    assets: "자산",
    assetsHint: "전체 보호 대상",
    openFindings: "미해결 발견사항",
    openFindingsHint: "처리 대기 중",
    scans7d: "스캔 (7일)",
    scans7dHint: "최근 7일",
    severityChart: "심각도별 미해결 발견사항",
    recentFindings: "최근 발견사항",
    recentScans: "최근 스캔",
  },

  assets: {
    title: "자산",
    add: "자산 추가",
    uri: "URI",
    env: "환경",
    owner: "담당",
    openFindings: "열린 발견",
    placeholderUri: "https://github.com/org/repo 또는 docker://image:tag",
    placeholderOwner: "팀 이름",
  },

  scans: {
    title: "스캔",
    trigger: "스캔 시작",
    triggerSelectAsset: "자산 선택",
    findingsCount: "발견 수",
    duration: "소요시간",
  },

  findings: {
    title: "발견사항",
    drawerNoInsight: "아직 AI 분석 결과가 없습니다. 'AI Triage 실행'을 눌러 분석을 시작하세요.",
    references: "참고 링크",
    remediation: "수정 가이드",
  },

  policies: {
    title: "정책",
    threshold: "임계치",
    compliance: "컴플라이언스",
    desc: "스캐너 결과에 적용되는 정책입니다. SAST / SCA / IaC / DAST / Container / Secrets / Compliance 유형 중 하나에 속하며, 임계치를 넘기는 발견사항은 파이프라인 게이트를 차단합니다.",
  },

  policySim: {
    title: "정책 시뮬레이션",
    desc: "이번 PR에 들어갈 가상 발견사항을 입력하면, 어떤 정책이 차단되는지 미리 확인합니다.",
    add: "발견 추가",
    ruleId: "Rule ID",
    simulate: "시뮬레이션 실행",
    result: "결과",
    blocked: "차단",
    passed: "통과",
  },

  ai: {
    title: "AI 인사이트",
    askPlaceholder: "Mond에게 무엇이든 물어보세요",
    askExample: "예: \"우리 nginx 이미지 스캔해줘\", \"이번 주 critical 이슈 뭐 있어?\"",
    enabled: "Claude 분석 활성",
    disabled: "ANTHROPIC_API_KEY 미설정 — 휴리스틱 모드",
    disabledHint: "실제 Claude 분석을 사용하려면 .env에 ANTHROPIC_API_KEY를 설정하고 백엔드를 재시작하세요.",
    analyze: "분석",
  },

  regulations: {
    title: "정보보안 규제 가이드",
    desc: "사업 시나리오를 고르면 적용되는 규제, 의무, 어느 시점에 무엇을 해야 하는지 한눈에 봅니다.",
    selectScenario: "사업 시나리오 선택",
    applicable: "적용 규제",
    obligations: "필수 의무",
    timings: "적용 시점",
    references: "참고 자료",
    downloadMd: "마크다운 리포트 다운로드",
  },

  reports: {
    title: "리포트",
    sbom: "SBOM 다운로드",
    sbomDesc: "선택한 자산의 발견사항을 CycloneDX-lite JSON 형식으로 받습니다.",
    compliance: "컴플라이언스 리포트",
    complianceDesc: "사업 시나리오별 규제 의무 + 현재 시스템 상태를 마크다운으로 받습니다.",
    pickAsset: "자산 선택",
    pickScenario: "시나리오 선택",
    downloadJson: "JSON 다운로드",
    downloadMarkdown: "마크다운 다운로드",
  },

  integrations: {
    title: "통합",
    scanners: "스캐너",
    ai: "AI",
    mcp: "MCP",
    mcpDesc: "Claude Desktop / Claude Code 등에서 Mond를 도구로 사용할 수 있습니다.",
    mcpStdio: "stdio (로컬)",
    mcpHttp: "HTTP+SSE (원격)",
    notifications: "알림 채널",
    notificationsDesc: ".env에 Slack/Generic Webhook URL을 채우면 Critical/High 발견사항을 자동 전송합니다.",
    webhookGithub: "GitHub Webhook",
    webhookGithubDesc: "POST /api/v1/webhooks/github 으로 push 이벤트를 보내면 해당 레포 자산을 자동 스캔합니다.",
  },

  settings: {
    title: "설정",
    serviceStatus: "서비스 상태",
    db: "데이터베이스",
    version: "버전",
    environment: "환경",
    ai: "AI",
    locale: "언어",
    note: "Mond OSS는 자율 호스팅을 전제로 합니다. 환경 변수는 .env에서, 운영 설정은 docker-compose.yml에서 관리하세요.",
  },
};

export type Dict = typeof ko;
