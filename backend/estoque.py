# flask --app estoque run --host 127.0.0.1 --port 8000

import pika
import json
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from flask import Flask, jsonify, request
from threading import Thread

# Carrega a chave pública do Principal
with open("keys/principal_public_key.pem", "rb") as key_file:
    public_key = serialization.load_pem_public_key(key_file.read())

estoque = [
    { "codigo": 123, "nome": "cerveja", "disponivel": 10, "valor":8 },
    { "codigo": 456, "nome": "refrigerante", "disponivel": 10, "valor":5 },
    { "codigo": 789, "nome": "água", "disponivel": 10, "valor":3 },
    { "codigo": 222, "nome": "vinho", "disponivel": 10, "valor":10 },
]

app = Flask(__name__)

@app.post("/estoque")
def confere_estoque():
    if not request.is_json:
        return {"resposta": "erro", "descricao": "erro no formato da requisição"}, 415
    
    item = request.get_json()
    for produto in estoque:
        if item["codigo"] == produto["codigo"] and item["quantidade"] > produto["disponivel"]:
            return {"resposta": "erro", "descricao": "produto fora de estoque"}
    return {"resposta": "ok"}

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

        print("Estoque atualizado:")
        print(estoque)

    except Exception as e:
        print(f" [!] Failed to verify message: {e}")

def ouvir_pedidos():
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

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

thread = Thread(target = ouvir_pedidos)
thread.start()