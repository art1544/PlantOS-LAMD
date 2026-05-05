# services/

Comunicação com API e mensageria RabbitMQ assíncrona (AMQP Direct - Filas exclusivas).

## Estrutura de Consumo:
O App se conectará ao RabbitMQ criando sua fila exclusiva temporária (ex: `queue_tec_456`) e a associará à exchange `plantos.events` (Direct) pelo `routing_key` correspondente ao seu `id` (ex: `tec_456`). Isso garante o recebimento de dados sem uso de *polling*.

