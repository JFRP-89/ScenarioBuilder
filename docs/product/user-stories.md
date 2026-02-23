# User Stories — Scenario Builder

## Convención

Formato: *Como [rol], quiero [acción] para [beneficio].*

Cada historia incluye criterios de aceptación y el use case que la resuelve.

---

## Generación de escenarios

### US-01: Generar escenario por seed

> Como jugador, quiero generar un escenario proporcionando un seed numérico
> para obtener un resultado determinista y reproducible.

**Criterios de aceptación:**
- Dado un seed válido (1–2³¹−1), el sistema genera siempre el mismo escenario.
- Seed 0 indica modo manual (no seeded).
- Seeds inválidos (negativos, booleanos, strings no numéricos) se rechazan con error claro.

**Use case:** `GenerateScenarioCard`

---

### US-02: Elegir modo de juego

> Como jugador, quiero seleccionar entre modos casual, narrative y matched
> para adaptar el escenario al tipo de partida.

**Criterios de aceptación:**
- `casual`: selección libre, sin restricciones de scoring.
- `narrative`: incluye twists y story hooks.
- `matched`: aplica scoring con penalización por risk flags.
- El modo afecta qué contenido MESBG se selecciona.

**Use case:** `GenerateScenarioCard`

---

### US-03: Configurar tamaño de mesa

> Como jugador, quiero especificar el tamaño de mi mesa (en cm, pulgadas o pies)
> para que el mapa se ajuste a mis condiciones reales.

**Criterios de aceptación:**
- Presets disponibles: Standard (120×120 cm), Massive (180×120 cm).
- Modo custom: dimensiones entre 60 y 300 cm por lado.
- Conversiones: 1 in = 2.5 cm, 1 ft = 30 cm.
- Máximo 2 decimales; se rechaza el uso de comas.

**Use case:** `GenerateScenarioCard`, `manage_presets`

---

## Renderizado SVG

### US-04: Visualizar mapa SVG

> Como jugador, quiero ver el mapa de mi escenario renderizado en SVG
> para visualizar la disposición de terreno y zonas de despliegue.

**Criterios de aceptación:**
- El SVG muestra 7 capas: fondo, grid, zonas, terreno, marcadores, etiquetas, marco.
- Incluye cotas dimensionales en los bordes.
- Incluye brújula cardinal (N/S/E/W).
- Se puede descargar como `.svg`.

**Use case:** `RenderMapSvg`

---

### US-05: Cambiar unidades de visualización

> Como jugador, quiero cambiar las unidades del mapa entre cm, pulgadas y pies
> para adaptarme a mi sistema de medida habitual.

**Criterios de aceptación:**
- Query param `display_units=cm|in|ft`.
- Las cotas se recalculan según la unidad elegida.
- El mapa SVG se re-renderiza sin cambiar las shapes.

**Use case:** `RenderMapSvg`

---

## Persistencia y gestión

### US-06: Guardar escenario

> Como jugador, quiero guardar un escenario generado para recuperarlo más tarde.

**Criterios de aceptación:**
- El escenario se persiste con un `card_id` único (UUID).
- Solo el owner autenticado puede guardar.
- Se almacenan: seed, mode, table, map_spec, deployment, objectives, constraints.

**Use case:** `SaveCard`

---

### US-07: Listar mis escenarios

> Como jugador, quiero ver una lista de mis escenarios guardados
> para encontrar y volver a usar mis favoritos.

**Criterios de aceptación:**
- Filtros: `mine`, `public`, `shared_with_me`.
- Cada item muestra: seed, modo, fecha de creación.
- Solo muestra cards a las que el usuario tiene acceso de lectura.

**Use case:** `ListCards`

---

### US-08: Ver detalle de escenario

> Como jugador, quiero ver todos los datos de un escenario
> para entender las reglas, deployment y objetivos antes de jugar.

**Criterios de aceptación:**
- Muestra: seed, modo, mesa, deployment, objective, twist, constraints, special rules.
- Incluye preview SVG del mapa.
- Anti-IDOR: retorna 403 si no tiene permisos.

**Use case:** `GetCard`

---

### US-09: Eliminar escenario

> Como jugador, quiero eliminar un escenario que ya no necesito
> para mantener mi galería organizada.

**Criterios de aceptación:**
- Solo el owner puede eliminar.
- Al eliminar, se limpian todos los favoritos asociados.
- Retorna 404 si no existe, 403 si no es owner.

**Use case:** `DeleteCard`

---

### US-10: Crear variante

> Como jugador, quiero clonar un escenario existente con un nuevo seed
> para explorar variaciones sin perder el original.

**Criterios de aceptación:**
- Genera nuevo `card_id` y seed.
- Mantiene configuración base (tabla, modo).
- Solo el owner del escenario base puede crear variantes.

**Use case:** `CreateVariant`

---

## Visibilidad y compartición

### US-11: Controlar visibilidad

> Como jugador, quiero elegir quién puede ver mis escenarios
> para mantener privacidad o compartir selectivamente.

**Criterios de aceptación:**
- Tres niveles: Private (solo yo), Shared (yo + lista), Public (todos).
- `shared_with` solo funciona con visibilidad `SHARED`.
- Cambio de visibilidad solo por el owner.

**Use case:** `SaveCard` (actualización de visibilidad)

---

### US-12: Marcar favoritos

> Como jugador, quiero marcar escenarios de otros usuarios como favoritos
> para accederlos rápidamente desde mi galería.

**Criterios de aceptación:**
- Toggle: si ya es favorito, lo quita; si no, lo añade.
- Requiere acceso de lectura al escenario.
- Al eliminar un escenario, los favoritos se limpian automáticamente.

**Use case:** `ToggleFavorite`, `ListFavorites`

---

## Autenticación

### US-13: Registrarse

> Como nuevo usuario, quiero crear una cuenta con username y email únicos
> para acceder al sistema.

**Criterios de aceptación:**
- Username: 3–32 caracteres, alfanumérico + guiones.
- Email: formato válido, único en el sistema.
- Password: 8+ caracteres, requiere mayúscula, número y carácter especial.
- Auto-login tras registro exitoso.

**Use case:** Auth service (`register`)

---

### US-14: Iniciar sesión

> Como usuario registrado, quiero iniciar sesión con username y contraseña
> para acceder a mis escenarios.

**Criterios de aceptación:**
- Login exitoso retorna `session_id` + `csrf_token`.
- 3 intentos fallidos consecutivos → cuenta bloqueada 1 hora.
- Mensajes genéricos (anti-enumeración).

**Use case:** Auth service (`authenticate`)

---

### US-15: Editar perfil

> Como usuario autenticado, quiero editar mi nombre, email o contraseña
> para mantener mi perfil actualizado.

**Criterios de aceptación:**
- Email actualizado debe ser único (excluyendo el propio usuario).
- Cambio de contraseña aplica la misma policy que el registro.
- Se validan todos los campos con allowlist.

**Use case:** Auth service (`update_profile`)
