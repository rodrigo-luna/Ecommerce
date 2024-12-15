import pika
import json
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from time import sleep

# Carrega a chave pública do Principal
with open("keys/pagamento_public_key.pem", "rb") as key_file:
    public_key = serialization.load_pem_public_key(key_file.read())

# Carrega a chave privada da Entrega
with open("keys/entrega_private_key.pem", "rb") as key_file:
    private_key = serialization.load_pem_private_key(
        key_file.read(),
        password=None,
)

# Conecta-se ao RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()
channel.exchange_declare(exchange='event_exchange', exchange_type='topic')
result = channel.queue_declare('', exclusive=True)
queue_name = result.method.queue

# Chaves de roteamento de interesse
binding_keys = [ "pagamentos.aprovados" ]
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

        sleep(10)
        pedido = json.loads(message)
        pedido["estado"] = "enviado"
        message = json.dumps(pedido)

        routing_key = "pedidos.enviados"

        signature = private_key.sign(
            message.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        # Publica a mensagem no RabbitMQ
        channel.basic_publish(
            exchange='event_exchange',
            routing_key=routing_key,
            body=message + "||" + signature.hex()  # Anexa a assinatura no final da mensagem
        )

        print(f" [x] Sent {routing_key}: {message} with signature")

    except Exception as e:
        print(f" [!] Failed to verify message: {e}")


channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

channel.start_consuming()