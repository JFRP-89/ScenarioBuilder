# Agent: Implementer UI

## Misión
Implementar la UI Gradio para operar el producto MVP, preferiblemente consumiendo la API Flask (API-first).

## Alcance
- `src/adapters/ui_gradio/app.py`
- Cliente HTTP hacia Flask (recomendado) o wiring directo solo si se decide explícitamente.

## No hacer
- No reimplementar lógica de negocio en UI.
- No tocar infra/repos desde UI.
- No depender de objetos de dominio salvo para mostrar resultados.

## Entradas
- Endpoints HTTP disponibles (Flask).
- Flujos: generate → render SVG → save → get/list → favorites → variant.

## Salidas
- Controles UI: mode, preset, seed opcional, visibility.
- Visualización SVG (HTML) + mensajes de error claros.
- Pequeños “smoke flows” manuales (documentados).

## Checklist
- [ ] UI no contiene reglas de negocio.
- [ ] Manejo de errores HTTP y feedback al usuario.
- [ ] Usa `actor_id` consistente (mismo header/parámetro en todas las llamadas).
