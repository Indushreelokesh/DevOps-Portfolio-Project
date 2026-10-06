{{- define "task-tracker.namespace" -}}
{{- .Values.namespace.name -}}
{{- end -}}

{{- define "task-tracker.labels" -}}
app.kubernetes.io/name: task-tracker
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}
