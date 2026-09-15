import threading
import time

from comum.core.pojos import NotaInformativa, TIPOS_DE_NOTA
from comum.core.servicos import (
    ErroDeServico,
    ServicoAutenticacao,
    administradores_de_exemplo,
    eleitores_de_exemplo,
)
from trabalho1_votacao.questao4_multicast.configuracao import (
    GRUPO_MULTICAST,
    PORTA_AUTENTICACAO,
    PORTA_MULTICAST,
)
from comum.sockets import PublicadorMulticast, ServidorRequisicaoResposta

servico_auth = ServicoAutenticacao()
publicador = PublicadorMulticast(GRUPO_MULTICAST, PORTA_MULTICAST)

clientes_autenticados: set = set()
trava_clientes = threading.Lock()

def publicar(tipo: str, mensagem: str) -> None:
    if tipo not in TIPOS_DE_NOTA:
        print(f"[servidor] tipo invalido: {tipo}. Use {TIPOS_DE_NOTA}.")
        return
    if publicador.publicar(NotaInformativa(tipo=tipo, mensagem=mensagem).para_dicionario()):
        print(f"[multicast] {tipo}: {mensagem}")

def login(dados, sessao):
    pessoa = servico_auth.autenticar(dados["login"], dados["senha"])
    sessao["login"] = pessoa.login

    with trava_clientes:
        clientes_autenticados.add(pessoa.login)

    print(f"[auth] {pessoa.login} autenticado")
    publicar("NOTIFICACAO", f"{pessoa.nome} entrou no grupo.")

    return {"nome": pessoa.nome, "grupo": GRUPO_MULTICAST, "porta": PORTA_MULTICAST}

def logout(dados, sessao):
    login_do_cliente = sessao.pop("login", None)
    if login_do_cliente:
        with trava_clientes:
            clientes_autenticados.discard(login_do_cliente)
        print(f"[auth] {login_do_cliente} saiu.")
    return {}

OPERACOES = {"LOGIN": login, "LOGOUT": logout}

AJUDA = """
Comandos do operador:
  n <mensagem>   envia NOTIFICACAO
  a <mensagem>   envia ALERTA
  u <mensagem>   envia ATUALIZACAO
  auto           dispara 3 mensagens seguidas em threads diferentes
                 (demonstra o envio concorrente exigido no item 4d)
  quem           lista clientes autenticados
  sair           encerra o servidor
"""

def console() -> None:
    while True:
        try:
            linha = input("servidor> ").strip()
        except EOFError:
            return
        if not linha:
            continue
        if linha == "sair":
            return

        if linha == "quem":
            with trava_clientes:
                lista = ", ".join(sorted(clientes_autenticados)) or "(ninguem)"
            print("  autenticados:", lista)
            continue

        if linha == "auto":

            for tipo, texto in (("NOTIFICACAO", "Votacao aberta."),
                                ("ALERTA", "Faltam 5 minutos para o encerramento!"),
                                ("ATUALIZACAO", "Novo candidato cadastrado.")):
                threading.Thread(target=publicar, args=(tipo, texto)).start()
            time.sleep(0.2)
            continue

        prefixo, _, texto = linha.partition(" ")
        tipos = {"n": "NOTIFICACAO", "a": "ALERTA", "u": "ATUALIZACAO"}
        if prefixo in tipos and texto:
            publicar(tipos[prefixo], texto)
        else:
            print(AJUDA)

def main() -> None:
    for eleitor in eleitores_de_exemplo():
        servico_auth.cadastrar_eleitor(eleitor)
    for admin in administradores_de_exemplo():
        servico_auth.cadastrar_administrador(admin)

    servidor = ServidorRequisicaoResposta(
        PORTA_AUTENTICACAO, OPERACOES, nome="auth",
        erros_de_negocio=(ErroDeServico,), registrar=False,
    )
    servidor.iniciar_em_thread()

    print(f"[servidor] TCP de autenticacao em {servidor.host}:{servidor.porta}")
    print(f"[servidor] Grupo multicast {GRUPO_MULTICAST}:{PORTA_MULTICAST}")
    print(AJUDA)

    console()

    servidor.parar()
    publicador.fechar()
    print("[servidor] Encerrado.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[servidor] Encerrado pelo usuario.")
