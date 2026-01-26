# SOLID checklist (práctico)

S — SRP: cada clase hace una cosa (repo / generator / renderer / use case).
O — OCP: añade features extendiendo (p.ej. nuevos generators) sin romper contratos.
L — LSP: implementaciones infra deben respetar ports.
I — ISP: ports pequeños y específicos (repos separados: cards vs favorites).
D — DIP: application depende de ports; infra los implementa.

Anti-patrones:
- adapter llamando a DB directo
- domain importando flask/gradio
- lógica de authz duplicada en 3 sitios
