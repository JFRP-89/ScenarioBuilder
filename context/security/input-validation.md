# Input validation

Adapters:
- Rechazar JSON inválido
- Strings vacíos/whitespace -> 400
- Seed: int >= 0 (si se provee)
- mode: casual/narrative/matched
- table_preset: standard/massive (custom más adelante)

Application/domain:
- Domain valida invariantes (MapSpec bounds, Card invariants, etc.)
- Application valida identity (actor_id/card_id) y orquesta.
- Evitar validar dos veces lo mismo sin motivo.
