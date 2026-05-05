# services/

Camada de lógica de negócio:

- **os_service.py** — Orquestra criação, transições de estado, validação de pré-condições e publicação de eventos no RabbitMQ

O service é o único ponto que chama o publisher de mensageria.
