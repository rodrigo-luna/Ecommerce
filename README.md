# Ecommerce
Sistema de um E-Commerce para a matéria de Sistemas Distribuídos da UTFPR. Inclui microsserviços, sistema de mensageria, API REST, SSE, WebHooks.

Instruções:
Instalar e configurar um servidor Redis rodando no localhost
cmd: "sudo service redis-server start"
(para verificar se o servidor está online: sudo service redis-server status)

Instalar o Flask e as outras dependências sendo importadas


NA PASTA BACKEND:

Iniciar a API
cmd: "flask run"

Iniciar a thread de Estoque
cmd: py -m estoque

Iniciar a thread de Pagamento
cmd: py -m pagamento

Iniciar a thread de Entrega
cmd: py -m entrega


NA PASTA FRONTEND:

Abrir o arquivo index.html
Adicionar ou remover itens do carrinho e gerar pedidos