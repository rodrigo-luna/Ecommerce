# app.py
from flask import Flask, request, jsonify
import json
import pika
from threading import Thread
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

# Carrega a chave pública do Pagamento
with open("keys/pagamento_public_key.pem", "rb") as key_file:
    pagamento_public_key = serialization.load_pem_public_key(key_file.read())

# Carrega a chave pública da Entrega
with open("keys/entrega_public_key.pem", "rb") as key_file:
    entrega_public_key = serialization.load_pem_public_key(key_file.read())

# Carrega a chave privada do Principal
with open("keys/principal_private_key.pem", "rb") as key_file:
    private_key = serialization.load_pem_private_key(
        key_file.read(),
        password=None,
)

app = Flask(__name__)

dados = [
    { "codigo": 123, "nome": "cerveja", "valor": 5 },
    { "codigo": 456, "nome": "refrigerante", "valor": 10 },
    { "codigo": 789, "nome": "agua", "valor": 3 },
    { "codigo": 222, "nome": "vinho", "valor": 15 },
]

# carrinho = []
carrinho = [
    { "codigo": 123, "quantidade": 1 },
    { "codigo": 456, "quantidade": 1 },
    { "codigo": 789, "quantidade": 1 },
]

pedidos = []

# Conecta-se ao RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()
channel.exchange_declare(exchange='event_exchange', exchange_type='topic')
result = channel.queue_declare('', exclusive=True)
queue_name = result.method.queue


##### CARRINHO #####

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

def callback(ch, method, properties, body):
    try:
        if method.routing_key == "pagamentos.aprovados":
            message, signature = body.decode().rsplit("||", 1)
            signature = bytes.fromhex(signature)
            pagamento_public_key.verify(
                signature,
                message.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )

            pedido = json.loads(message)
            pedidos[pedido["id"]-1]["estado"] = "pagamento aprovado"
            print("Avisando o cliente que o pagamento foi aprovado")

        elif method.routing_key == "pagamentos.recusados":
            message, signature = body.decode().rsplit("||", 1)
            signature = bytes.fromhex(signature)
            pagamento_public_key.verify(
                signature,
                message.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )

            pedido = json.loads(message)
            pedidos[pedido["id"]-1]["estado"] = "pagamento recusado"
            print("Avisando o cliente que o pagamento foi recusado")
    
        elif method.routing_key == "pedidos.enviados":
            message, signature = body.decode().rsplit("||", 1)
            signature = bytes.fromhex(signature)
            entrega_public_key.verify(
                signature,
                message.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )

            pedido = json.loads(message)
            pedidos[pedido["id"]-1]["estado"] = "enviado"
            print("Avisando o cliente que o pedido foi enviado")

            
        print(f" [x] Verified {method.routing_key}: {message}")

    except Exception as e:
        print(f" [!] Failed to verify message: {e}")

def acompanhar_pedido(pedido):
    print("teste")
    # Define a chave de roteamento e a mensagem
    routing_key = 'pedidos.criados'
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

    # Chaves de roteamento de interesse
    binding_keys = [ "pagamentos.aprovados", "pagamentos.recusados", "pedidos.enviados" ]
    for binding_key in binding_keys:
        channel.queue_bind(exchange='event_exchange', queue=queue_name, routing_key=binding_key)

    print(' [*] Waiting for events. To exit press CTRL+C')

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

    channel.start_consuming()


@app.post("/pedidos")
def add_pedido():
    pedido = { "id": _find_next_id(), "estado": "esperando pagamento", "itens": carrinho.copy() }
    pedidos.append(pedido)
    carrinho.clear()
        
    thread = Thread(target = acompanhar_pedido, args = (pedido,))
    thread.start()

    return pedido, 201
