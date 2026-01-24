# SOLID Review Checklist

## Purpose
Revisión rápida de diseño para evitar code smells en crecimiento.

## S — Single Responsibility
- ¿Este módulo/clase tiene un único motivo de cambio?
- ¿Mezcla validación + IO + reglas? => separar.

## O — Open/Closed
- ¿Puedo añadir una regla/estrategia sin modificar 10 sitios?
- Preferir estrategias/handlers en domain.

## L — Liskov
- Si hay interfaces/puertos: ¿las implementaciones respetan el contrato?

## I — Interface Segregation
- Puertos pequeños: ¿evito “Repository” gigante con 20 métodos?

## D — Dependency Inversion
- application depende de puertos, no de Postgres/Flask/filesystem.

## Smells comunes y acciones
- Duplicación -> helper/constantes
- Magic numbers -> constants/config en domain
- Condicionales complejos -> extraer función/estrategia

## How to verify
- Refactor con tests verdes
- Review PR con esta checklist
