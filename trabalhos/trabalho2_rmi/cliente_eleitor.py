import sys

from comum.rmi import ErroRemotoRMI
from trabalho2_rmi.cliente_base import ClienteRMI

MENU = """
[1] listar candidatos   [2] votar   [3] apuracao parcial
[4] ja votei?           [5] historico de notas          [0] sair"""

def main() -> None:
    login = sys.argv[1] if len(sys.argv) > 1 else "kleyton"
    senha = sys.argv[2] if len(sys.argv) > 2 else "123"

    cliente = ClienteRMI(login, senha)
    try:
        if not cliente.entrar():
            return
        if cliente.e_admin:
            print("Este cliente e' so' para eleitores. Use o cliente_admin.")
            return

        while True:
            print(MENU)
            escolha = input("> ").strip()
            try:
                if escolha == "1":
                    for c in cliente.urna.listar_candidatos():
                        print(f"  {c.numero:>3} - {c.nome} ({c.partido})")
                    print(f"  prazo restante: {cliente.urna.segundos_restantes()}s")

                elif escolha == "2":
                    numero = int(input("numero do candidato: ").strip())
                    voto = cliente.sessao.votar(numero)
                    print(f"  Voto registrado em {voto.numero_candidato}. Obrigado!")

                elif escolha == "3":
                    apuracao = cliente.urna.apurar()
                    for linha in apuracao["resultado"]:
                        print(f"  {linha['numero']:>3} {linha['nome']:<16} "
                              f"{linha['votos']:>3} voto(s)  {linha['percentual']}%")
                    print(f"  total: {apuracao['total_de_votos']} | "
                          f"encerrada: {'sim' if apuracao['encerrada'] else 'nao'}")

                elif escolha == "4":
                    print("  ja votei?", "sim" if cliente.sessao.ja_votei() else "nao")

                elif escolha == "5":
                    for nota in cliente.painel.historico():
                        print(f"  <{nota.tipo}> {nota.mensagem}")

                elif escolha == "0":
                    break
                else:
                    print("  opcao invalida.")

            except ErroRemotoRMI as erro:

                print("  ERRO:", erro.mensagem)
            except ValueError:
                print("  numero invalido.")
            print()

    except (EOFError, KeyboardInterrupt):
        pass
    except (ConnectionRefusedError, OSError):
        print("Servidor fora do ar. Rode: python3 -m trabalho2_rmi.servidor")
        return
    finally:
        cliente.sair()

if __name__ == "__main__":
    main()
