{{/*
Database environment shared by the lm-api container and the migration init container.
DATABASE_NAME is only set when multi-tenancy is disabled. With multi-tenancy, the
database is selected per request from the organization id in the token.
*/}}
{{- define "lm-api.dbEnv" -}}
- name: MULTI_TENANCY_ENABLED
  value: {{ .Values.multiTenancy.enabled | quote }}
{{- if not .Values.multiTenancy.enabled }}
- name: DATABASE_NAME
  value: {{ .Values.postgres.database | quote }}
{{- end }}
- name: DATABASE_PSWD
  valueFrom:
    secretKeyRef:
      name: lm-kubegres-credentials
      key: primary-password
- name: DATABASE_HOST
  value: lm-postgres
- name: DATABASE_USER
  value: omnivector
- name: DATABASE_PORT
  value: "5432"
{{- end }}
