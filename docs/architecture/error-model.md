# Modelo de Errores

## Principio

Los errores de dominio son **semánticos** (qué falló), no técnicos (cómo se
transporta).  
El mapeo a códigos HTTP ocurre **exclusivamente** en la capa de adapters.

---

## Jerarquía

```
Exception
 └── DomainError          ← Base (src/domain/errors.py)
      ├── ValidationError  ← Input inválido / invariante roto
      ├── NotFoundError    ← Entidad no encontrada
      └── ForbiddenError   ← Permisos insuficientes
```

---

## Uso por capa

### Domain

Lanza `ValidationError` en `__post_init__` y funciones de validación:

```python
# domain/cards/card_validation.py
def validate_seed(value):
    if isinstance(value, bool):
        raise ValidationError("seed must not be a boolean")
    if not isinstance(value, int):
        raise ValidationError("seed must be an integer")
    if value < 0:
        raise ValidationError("seed must be non-negative")
```

### Application

Los use cases propagan `ValidationError` del domain y lanzan `NotFoundError` /
`ForbiddenError` cuando corresponde:

```python
# application/use_cases/get_card.py
def execute(self, request):
    card = self.repo.get_by_id(request.card_id)
    if card is None:
        raise NotFoundError(f"Card {request.card_id} not found")
    if not card.can_user_read(request.actor_id):
        raise ForbiddenError("Access denied")
    return GetCardResponse(...)
```

### Adapters (Flask)

Único lugar donde se mapean errores a HTTP:

```python
# adapters/http_flask/error_contract.py
@app.errorhandler(ValidationError)
def handle_validation(e):
    return jsonify({"error": str(e)}), 400

@app.errorhandler(NotFoundError)
def handle_not_found(e):
    return jsonify({"error": str(e)}), 404

@app.errorhandler(ForbiddenError)
def handle_forbidden(e):
    return jsonify({"error": str(e)}), 403
```

| Error de dominio | Código HTTP | Cuándo |
|-----------------|-------------|--------|
| `ValidationError` | `400 Bad Request` | Input inválido, invariante roto |
| `NotFoundError` | `404 Not Found` | Card/User no existe |
| `ForbiddenError` | `403 Forbidden` | Sin permisos |
| `Exception` (fallback) | `500 Internal Server Error` | Error inesperado |

### Adapters (Gradio)

Los errores se capturan y muestran como mensajes en la interfaz (no HTTP):

```python
try:
    result = service.execute(request)
except ValidationError as e:
    return gr.Warning(str(e))
```

---

## Reglas

1. **Domain/application NUNCA retornan códigos HTTP.**
2. **Adapters NUNCA lanzan `ValidationError`** — la reciben y la transforman.
3. **Los mensajes de error son descriptivos pero NO revelan datos internos**
   (IDs de BD, stack traces, rutas de archivos).
4. **Anti-enumeración**: en autenticación, los errores son genéricos
   ("credenciales inválidas"), no "usuario no encontrado" vs "contraseña incorrecta".
