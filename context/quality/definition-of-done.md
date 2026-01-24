# Definition of Done (DoD)

## Purpose
Un PR “listo” es verificable, seguro, documentado y no rompe gates.

## DoD checklist
- [ ] Tests relevantes añadidos/actualizados
- [ ] `make lint && make test` pasa
- [ ] Coverage gates (domain 100 / application >=80) pasan
- [ ] No se añadieron deps sin `requirements.txt`
- [ ] Si cambia superficie de entrada/seguridad → threat model actualizado
- [ ] Si el cambio es notable → `CHANGELOG.md` actualizado en `[Unreleased]`

## Recommended verify (local)
- `make lint && make test`
- (si runtime) `docker compose up` y smoke `/health`

## How to verify
- CI verde en PR
- Checklist completada en template
