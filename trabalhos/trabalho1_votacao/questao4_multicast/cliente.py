import sys

from trabalho1_votacao.questao4_multicast.configuracao import PORTA_AUTENTICACAO
from comum.sockets import ClienteTCP, ErroRemoto, OuvinteMulticast
from comum.sockets.multicast import formatar_nota

HOST_SERVIDOR = "127.0.0.1"

def exibir(nota, remetente) -> None:
    print(f"\n  {formatar_nota(nota, remetente)}\n> ", end="", flush=True)

def main() -> None:
    login = sys.argv[1] if len(sys.argv) > 1 else "kleyton"
    senha = sys.argv[2] if len(sys.argv) > 2 else "123"

    cliente = ClienteTCP(HOST_SERVIDOR, PORTA_AUTENTICACAO)
    ouvinte = None
    try:

        with cliente:
            dados = cliente.chamar("LOGIN", login=login, senha=senha)
            print(f"Autenticado como {dados['nome']}.")

            ouvinte = OuvinteMulticast(dados["grupo"], dados["porta"], exibir)
            if not ouvinte.entrar():
                return
            ouvinte.iniciar()
            print(f"Entrei no grupo {dados['grupo']}:{dados['porta']} (joinGroup).")

            print("\nComandos: [sair] leaveGroup e encerrar | [status] situacao")
            print("Fique com este terminal aberto: as mensagens aparecem sozinhas.\n")
            while True:
                comando = input("> ").strip().lower()
                if comando == "sair":
                    break
                if comando == "status":
                    print(f"  login={login} | grupo={ouvinte.grupo}")
                elif comando:
                    print("  comandos: sair | status")

            cliente.chamar("LOGOUT")

    except ErroRemoto as erro:
        print("Falha:", erro)
    except (EOFError, KeyboardInterrupt):
        pass
    except ConnectionRefusedError:
        print("Servidor fora do ar. Rode: python3 -m trabalho1_votacao.questao4_multicast.servidor")
        return
    finally:
        if ouvinte is not None:
            ouvinte.sair()
            print("Sai do grupo (leaveGroup).")
        print("Cliente encerrado.")

if __name__ == "__main__":
    main()
