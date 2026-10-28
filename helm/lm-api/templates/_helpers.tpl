{{/*
CloudNativePG names the Service and the app Secret of a Cluster after the
Cluster itself. The Cluster is named "lm-postgres" in cnpg.yaml.
*/}}
{{- define "lm.dbHost" -}}
lm-postgres-rw
{{- end -}}

{{- define "lm.dbSecretName" -}}
lm-postgres-app
{{- end -}}

{{/*
Database environment shared by the lm-api container and the migration init container.
DATABASE_NAME is only set when multi-tenancy is disabled. With multi-tenancy, the
database is selected per request from the organization id in the token.
DATABASE_USER/DATABASE_PSWD come from the Secret CloudNativePG generates for the
Cluster's app user (see lm.dbSecretName).
*/}}
{{- define "lm-api.dbEnv" -}}
- name: MULTI_TENANCY_ENABLED
  value: {{ .Values.multiTenancy.enabled | quote }}
{{- if not .Values.multiTenancy.enabled }}
- name: DATABASE_NAME
  value: {{ .Values.postgres.database | quote }}
{{- end }}
- name: DATABASE_USER
  valueFrom:
    secretKeyRef:
      name: {{ include "lm.dbSecretName" . }}
      key: username
- name: DATABASE_PSWD
  valueFrom:
    secretKeyRef:
      name: {{ include "lm.dbSecretName" . }}
      key: password
- name: DATABASE_HOST
  value: {{ include "lm.dbHost" . }}
- name: DATABASE_PORT
  value: "5432"
{{- end }}
