# routes/

Blueprints Flask com os endpoints REST:

- **os_routes.py** — CRUD de OS (POST, GET, PATCH) + endpoints de materiais

Cada endpoint valida a entrada, delega ao service e retorna JSON.
Transições de estado inválidas retornam 409 Conflict.
