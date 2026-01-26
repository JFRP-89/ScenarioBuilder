# Definition of Done (DoD)

Para dar algo por “hecho”:
- [ ] Tests target en verde (unit/integration según alcance)
- [ ] Suite completa pasa (`pytest -q`)
- [ ] Lint pasa (`ruff check ...`) si aplica
- [ ] No hay imports `src.` nuevos
- [ ] No hay lógica de negocio en adapters
- [ ] Seguridad: deny-by-default y anti-IDOR en casos de lectura/escritura
- [ ] CHANGELOG actualizado si es cambio notable
