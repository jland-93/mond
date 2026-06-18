{{/* 공용 헬퍼 */}}

{{- define "mond.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "mond.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{- define "mond.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" }}
app.kubernetes.io/name: {{ include "mond.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{- define "mond.selectorLabels" -}}
app.kubernetes.io/name: {{ include "mond.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "mond.image.tag" -}}
{{- .Values.image.tag | default .Chart.AppVersion -}}
{{- end -}}

{{- define "mond.backend.image" -}}
{{- printf "%s/%s-backend:%s" .Values.image.registry .Values.image.repository (include "mond.image.tag" .) -}}
{{- end -}}

{{- define "mond.frontend.image" -}}
{{- printf "%s/%s-frontend:%s" .Values.image.registry .Values.image.repository (include "mond.image.tag" .) -}}
{{- end -}}

{{- define "mond.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- default (include "mond.fullname" .) .Values.serviceAccount.name -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}

{{- define "mond.secretName" -}}
{{- if .Values.secrets.existingSecret -}}
{{- .Values.secrets.existingSecret -}}
{{- else -}}
{{- printf "%s-secrets" (include "mond.fullname" .) -}}
{{- end -}}
{{- end -}}

{{/* in-cluster postgres 사용 여부에 따라 DATABASE_URL 자동 합성 */}}
{{- define "mond.databaseUrl" -}}
{{- if .Values.postgresql.enabled -}}
postgresql+asyncpg://{{ .Values.postgresql.auth.username }}:{{ .Values.postgresql.auth.password }}@{{ .Release.Name }}-postgresql:5432/{{ .Values.postgresql.auth.database }}
{{- else -}}
{{ .Values.secrets.databaseUrl }}
{{- end -}}
{{- end -}}

{{- define "mond.redisUrl" -}}
{{- if .Values.redis.enabled -}}
redis://{{ .Release.Name }}-redis-master:6379/0
{{- else -}}
{{ .Values.secrets.redisUrl }}
{{- end -}}
{{- end -}}
