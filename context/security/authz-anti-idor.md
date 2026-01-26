# Anti-IDOR (AuthZ)

Objetivo: impedir acceso por “adivinar IDs”.

Reglas típicas:
- GetCard:
  - owner siempre puede leer
  - public: cualquiera puede leer
  - private: solo owner
- SaveCard:
  - solo owner puede escribir
- ListCards:
  - mine / public / shared_with_me (cuando exista SHARED)

En adapters:
- `actor_id` viene del header `X-Actor-Id` (o equivalente).
- Nunca confíes en `owner_id` del payload: se deriva del actor.
