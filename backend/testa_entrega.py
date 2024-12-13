# app.py
from flask import Flask, request, jsonify
import json
import pika
import sys
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization


with open("keys/principal_private_key.pem", "rb") as key_file:
    private_key = serialization.load_pem_private_key(
        key_file.read(),
        password=None,
)
    
# Conecta-se ao RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()
channel.exchange_declare(exchange='event_exchange', exchange_type='topic')

# Define a chave de roteamento e a mensagem
routing_key = "pedidos.aprovados"

pedido = {
    "id": 1,
    "estado": "aprovado",
    "itens": [
        { "codigo": 123, "quantidade": 1 },
        { "codigo": 456, "quantidade": 1 },
        { "codigo": 789, "quantidade": 1 }
    ]   
}
message = json.dumps(pedido)

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
connection.close()