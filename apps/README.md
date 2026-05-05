# apps/

Aplicativos móveis Flutter (Dart) do PlantOS:

- **operator/** — App do Operador (cliente que abre OS)
- **technician/** — App do Técnico (prestador que executa OS)

Ambos seguem Clean Architecture (models → services → screens) e são offline-first com SQLite local + outbox pattern.
