# app.py
from flask import Flask, request, jsonify
import json
import pika
import sys
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization

# Carrega a chave privada do publicador
with open("private_key.pem", "rb") as key_file:
    private_key = serialization.load_pem_private_key(
        key_file.read(),
        password=None,
)

app = Flask(__name__)

dados = [
    { "codigo": 123, "nome": "cerveja", "valor": 5 },
    { "codigo": 456, "nome": "refrigerante", "valor": 10 },
    { "codigo": 789, "nome": "agua", "valor": 3 },
    { "codigo": 222, "nome": "vinha", "valor": 15 },
]

# carrinho = []
carrinho = [
    { "codigo": 123, "quantidade": 1 },
    { "codigo": 456, "quantidade": 1 },
    { "codigo": 789, "quantidade": 1 },
]

pedidos = []

def get_produto_by_codigo(cod):
    for i in range(len(carrinho)):
        if carrinho[i]["codigo"] == int(cod):
            return i
    return -1

@app.get("/carrinho")
def get_carrinho():
    return jsonify(carrinho)

@app.post("/carrinho")
def add_produto():
    if not request.is_json:
        return {"erro": "Erro no formato da requisição"}, 415
    
    produto = request.get_json()
    carrinho.append(produto)
    return produto, 201

@app.route("/carrinho/<int:cod>/", methods= ["DELETE"])
def delete_produto(cod):
    index = get_produto_by_codigo(cod)
    if index == -1:
        return {"erro": "Produto código [" + str(cod) + "] não encontrado"}, 400
    
    del carrinho[index]
    return {"sucesso": "Produto código [" + str(cod) + "] removido"}, 200
    
@app.route("/carrinho/<int:cod>/", methods= ["PUT"])
def put_produto(cod):
    if not request.is_json:
        return {"erro": "Erro no formato da requisição"}, 415
    
    index = get_produto_by_codigo(cod)
    if index == -1:
        return {"erro": "Produto código [" + str(cod) + "] não encontrado"}, 400
    
    produto = request.get_json()
    carrinho[index].update(produto)
    return carrinho[index], 200


##### PEDIDOS #####

def _find_next_id():
    if len(pedidos) == 0:
        return 1
    return max(pedido["id"] for pedido in pedidos) + 1

def get_pedido_by_id(id):
    for i in range(len(pedidos)):
        if pedidos[i]["id"] == int(id):
            return i
    return -1

@app.get("/pedidos")
def get_pedidos():
    return jsonify(pedidos)

@app.post("/pedidos")
def add_pedido():
    pedido = { "id": _find_next_id(), "itens": carrinho.copy() }
    pedidos.append(pedido)
    carrinho.clear()
        
    # Conecta-se ao RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    # Declara o exchange
    channel.exchange_declare(exchange='event_exchange', exchange_type='topic')

    # Define a chave de roteamento e a mensagem
    routing_key = 'pedidos.criados'
    message = json.dumps(pedido)

    # Assina a mensagem digitalmente
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

    return pedido, 201
