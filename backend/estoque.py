import pika
import json
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


estoque = [
    { "codigo": 123, "disponivel": 10 },
    { "codigo": 456, "disponivel": 10 },
    { "codigo": 789, "disponivel": 10 },
    { "codigo": 222, "disponivel": 10 },
]

# Carrega a chave pública do Principal
with open("keys/principal_public_key.pem", "rb") as key_file:
    public_key = serialization.load_pem_public_key(key_file.read())

# Conecta-se ao RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()
channel.exchange_declare(exchange='event_exchange', exchange_type='topic')
result = channel.queue_declare('', exclusive=True)
queue_name = result.method.queue

# Chaves de roteamento de interesse
binding_keys = [ "pedidos.criados", "pedidos.excluidos" ]
for binding_key in binding_keys:
    channel.queue_bind(exchange='event_exchange', queue=queue_name, routing_key=binding_key)

print(' [*] Waiting for events. To exit press CTRL+C')

def callback(ch, method, properties, body):
    try:
        message, signature = body.decode().rsplit("||", 1)
        signature = bytes.fromhex(signature)
        public_key.verify(
            signature,
            message.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        print(f" [x] Verified {method.routing_key}: {message}")

        pedido = json.loads(message)
        if method.routing_key == "pedidos.criados":
            for item in pedido["itens"]:
                if item["codigo"] == 123:
                    estoque[0]["disponivel"] -= item["quantidade"]
                elif item["codigo"] == 456:
                    estoque[1]["disponivel"] -= item["quantidade"]
                elif item["codigo"] == 789:
                    estoque[2]["disponivel"] -= item["quantidade"]
                elif item["codigo"] == 222:
                    estoque[3]["disponivel"] -= item["quantidade"]

        elif method.routing_key == "pedidos.excluidos":
            for item in pedido["itens"]:
                if item["codigo"] == 123:
                    estoque[0]["disponivel"] += item["quantidade"]
                elif item["codigo"] == 456:
                    estoque[1]["disponivel"] += item["quantidade"]
                elif item["codigo"] == 789:
                    estoque[2]["disponivel"] += item["quantidade"]
                elif item["codigo"] == 222:
                    estoque[3]["disponivel"] += item["quantidade"]

        print("Novo estoque:")
        print(estoque)

    except Exception as e:
        print(f" [!] Failed to verify message: {e}")


channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

channel.start_consuming()



# estoque = [
#     { "codigo": 123, "disponivel": 10, "nome": "cerveja" },
#     { "codigo": 456, "disponivel": 10, "nome": "refrigerante" },
#     { "codigo": 789, "disponivel": 10, "nome": "agua" },
#     { "codigo": 222, "disponivel": 10, "nome": "vinho" },
# ]