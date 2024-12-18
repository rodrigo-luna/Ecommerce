
var qtd_cerveja = 0, qtd_refri = 0, qtd_agua = 0, qtd_vinho = 0;
var val_cerveja = 8, val_refri = 5, val_agua = 3, val_vinho = 10;
var cod_cerveja = "123", cod_refri = "456", cod_agua = "789", cod_vinho = "222";


var source = new EventSource('http://127.0.0.1:5000/eventos');
source.onmessage = function (event) {
    alert(event.data);
};

function cerveja(n) {
    if (qtd_cerveja == 0 && n == -1)
        return

    qtd_cerveja += n
    atualizar_item("cerveja")
    enviar_alteracao(cod_cerveja, qtd_cerveja, n)
}

function refri(n) {
    if (qtd_refri == 0 && n == -1)
        return

    qtd_refri += n
    atualizar_item("refri")
    enviar_alteracao(cod_refri, qtd_refri, n)
}

function agua(n) {
    if (qtd_agua == 0 && n == -1)
        return

    qtd_agua += n
    atualizar_item("agua")
    enviar_alteracao(cod_agua, qtd_agua, n)
}

function vinho(n) {
    if (qtd_vinho == 0 && n == -1)
        return

    qtd_vinho += n
    atualizar_item("vinho")
    enviar_alteracao(cod_vinho, qtd_vinho, n)
}

function fazer_pedido() {
    if (qtd_agua + qtd_cerveja + qtd_refri + qtd_vinho == 0)
        return

    fetch("http://127.0.0.1:5000/pedidos", {
        method: "POST",
        body: "",
        headers: {
            "Content-type": "application/json; charset=UTF-8"
        }
    })
    .then((response) => response.json())
    .then((json) => console.log(json));

    
    qtd_cerveja = 0, qtd_refri = 0, qtd_agua = 0, qtd_vinho = 0
    atualizar_item("cerveja")
    atualizar_item("refri")
    atualizar_item("agua")
    atualizar_item("vinho")
}

function check_carrinho_vazio() {
    if (qtd_agua + qtd_cerveja + qtd_refri + qtd_vinho == 0)
        document.getElementById("vazio").style.display = "block"
    else
        document.getElementById("vazio").style.display = "none"
}

function atualizar_item(item) {
    if (item == "cerveja") {
        document.getElementById("qtd_cerveja").innerHTML = qtd_cerveja
        document.getElementById("val_cerveja").innerHTML = "R$" + qtd_cerveja*val_cerveja
        
        if (qtd_cerveja == 0)   
            document.getElementById("cerveja").style.display = "none"
        else
            document.getElementById("cerveja").style.display = "grid"
    }
    else if (item == "refri") {
        document.getElementById("qtd_refri").innerHTML = qtd_refri;
        document.getElementById("val_refri").innerHTML = "R$" + qtd_refri*val_refri;
        
        if (qtd_refri == 0)   
            document.getElementById("refri").style.display = "none"
        else
            document.getElementById("refri").style.display = "grid"
    }
    else if (item == "agua") {
        document.getElementById("qtd_agua").innerHTML = qtd_agua;
        document.getElementById("val_agua").innerHTML = "R$" + qtd_agua*val_agua;
        
        if (qtd_agua == 0)   
            document.getElementById("agua").style.display = "none"
        else
            document.getElementById("agua").style.display = "grid"
    }
    else if (item == "vinho") {
        document.getElementById("qtd_vinho").innerHTML = qtd_vinho;
        document.getElementById("val_vinho").innerHTML = "R$" + qtd_vinho*val_vinho;
        
        if (qtd_vinho == 0)   
            document.getElementById("vinho").style.display = "none"
        else
            document.getElementById("vinho").style.display = "grid"
    }

    check_carrinho_vazio()
}

function enviar_alteracao(cod, qtd, n) {
    if (qtd == 1 && n==1) {
        fetch("http://127.0.0.1:5000/carrinho", {
            method: "POST",
            body: JSON.stringify({
                "codigo": cod,
                "quantidade": qtd
            }),
            headers: {
                "Content-type": "application/json; charset=UTF-8"
            }
            })
            .then((response) => response.json())
            .then((json) => console.log(json));
    }
    else if (qtd == 0 && n==-1) {
        fetch("http://127.0.0.1:5000/carrinho/" + cod, {
            method: "DELETE",
            body: "",
            headers: {
                "Content-type": "application/json; charset=UTF-8"
            }
            })
            .then((response) => response.json())
            .then((json) => console.log(json));
    }
    else {
        fetch("http://127.0.0.1:5000/carrinho/" + cod, {
            method: "PUT",
            body: JSON.stringify({
                "quantidade": qtd
            }),
            headers: {
                "Content-type": "application/json; charset=UTF-8"
            }
            })
            .then((response) => response.json())
            .then((json) => console.log(json));
    }
}