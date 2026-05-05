# services/

Comunicação com API e mensageria RabbitMQ assíncrona (AMQP Direct - Filas exclusivas).

## Estrutura de Consumo:
O App se conectará ao RabbitMQ criando sua fila exclusiva temporária (ex: `queue_op_123`) via `dart_amqp` e a associará a exchange `plantos.events` (Direct) pelo `routing_key` correspondente ao seu `id` (ex: `op_123`).

