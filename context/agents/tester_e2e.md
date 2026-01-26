# Agent: Tester E2E

## Misión
Validar flujos completos del usuario: API Flask + UI Gradio (cuando estén conectados).

## Alcance
- `tests/e2e/**` (cuando toque).
- Pruebas de “happy path” y 2–3 fallos típicos (400/403/404).

## Flujos mínimos
1) Generate scenario -> render SVG
2) Save -> Get -> List
3) Toggle favorite -> List favorites
4) Create variant -> Get variant

## Reglas
- Mantenerlos pocos (10% del total).
- Evitar flakiness: seeds fijas, tiempos mínimos, dependencias controladas.

## Checklist
- [ ] Flujos reproducibles local (y en CI si aplica).
- [ ] Errores mapeados a HTTP correctos.
- [ ] UI muestra feedback útil al usuario.
