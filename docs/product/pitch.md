# Pitch — Scenario Builder

## Elevator Pitch

> Scenario Builder es un **generador de escenarios tácticos** para wargames de
> miniaturas que produce mapas SVG reproducibles, ajustados al tamaño real de
> mesa del jugador.

---

## El problema

Los jugadores de wargames (MESBG, Warhammer, etc.) dedican **30–60 minutos**
antes de cada partida a montar el escenario: elegir misión, colocar terreno,
decidir zonas de despliegue, definir reglas especiales. Esto genera:

- **Fatiga de decisión**: demasiadas combinaciones posibles sin guía.
- **Repetición**: los jugadores tienden a repetir los mismos escenarios.
- **Desequilibrio**: sin validación, las combinaciones pueden ser injustas.
- **Falta de registro**: los escenarios se pierden al terminar la partida.

## La solución

Scenario Builder automatiza la generación de escenarios con un **motor
determinista** basado en seeds:

1. **Mismo seed = mismo escenario**, siempre. Ideal para torneos y replay.
2. **Validación de reglas**: el dominio verifica compatibilidad de constraints,
   balance de escenografía, límites de mesa y scoring.
3. **SVG a escala real**: imprimible 1:1, con cotas (acotaciones), brújula y
   leyenda de zonas.
4. **Tres modos de juego**:
   - `casual` — todo vale, libertad total.
   - `narrative` — elementos narrativos (twists, story hooks).
   - `matched` — reglas competitivas con scoring anti-desequilibrio.

## Diferenciación

| Característica | Scenario Builder | Alternativas (PDFs, apps genéricas) |
|---------------|-----------------|-------------------------------------|
| Reproducibilidad | ✅ Seed determinista | ❌ Aleatorio sin registro |
| Validación de reglas | ✅ En dominio puro | ❌ Manual por los jugadores |
| SVG escalable | ✅ Imprimible a tamaño real | ❌ Imágenes raster fijas |
| Multi-modo | ✅ casual/narrative/matched | ❌ Un solo modo |
| Compartir escenarios | ✅ Private/shared/public | ❌ No soportado |
| Anti-IDOR / seguridad | ✅ Deny-by-default | ❌ No aplica |

## Público objetivo

- **Jugadores de MESBG** (Middle Earth Strategy Battle Game) — target primario.
- **Organizadores de torneos** — seeds reproducibles para rondas.
- **Comunidades online** — compartir escenarios con visibilidad granular.
- **Otros wargames** (roadmap) — Warhammer, Bolt Action, etc.

## Estado actual

- **MVP funcional**: generación, guardado, galería, favoritos, perfil.
- **3064+ tests** pasando (1972 unit + 1000+ integration + 100+ e2e) con BD habilitada.
- **Quality gates**: ruff, black, mypy strict, bandit SAST — **all passing**.
- **Clean Architecture** con TDD y Security by Design.
- **Cobertura verificada**: Domain 100%, Application 99%.
- **Docker ready**: `docker compose up` para stack completo.

## Visión a futuro

- Export a PDF/imagen para juego offline.
- Wizard UX con presets de mesa y figuras.
- Soporte multi-juego (más allá de MESBG).
- Modo torneo con brackets y seeds por ronda.
