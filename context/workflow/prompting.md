# Prompting estándar (Codex/Copilot)

Formato recomendado:
1) Objetivo (1–2 frases)
2) Restricciones (qué NO tocar / deps / alcance)
3) Archivos permitidos (lista exacta)
4) Contrato esperado (API/DTO/ports)
5) Tests target (comando pytest)
6) Entrega (qué archivo devolver)

Plantillas rápidas:
- RED: “Crea SOLO tests en X. Prohibido tocar src/. Imports lazy. Da igual que fallen.”
- GREEN: “Implementa X en src/... para pasar tests Y. No toques tests. Minimal, sin deps.”
- Migración: “Mantén compat temporal, introduce ruta moderna y marca legacy para purge posterior.”
