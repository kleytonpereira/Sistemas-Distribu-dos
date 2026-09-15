import sys

from comum.rmi import ErroRemotoRMI
from trabalho2_rmi.cliente_base import ClienteRMI

MENU = """
[1] adicionar candidato   [2] remover candidato   [3] publicar nota
[4] listar candidatos     [5] apuracao            [6] quem esta inscrito
[0] sair"""

def main() -> None:
    login = sys.argv[1] if len(sys.argv) > 1 else "admin"
    senha = sys.argv[2] if len(sys.argv) > 2 else "admin"

    cliente = ClienteRMI(login, senha)
    try:
        if not cliente.entrar():
            return
        if not cliente.e_admin:
            print("Este cliente e' so' para administradores.")
            return

        while True:
            print(MENU)
            escolha = input("> ").strip()
            try:
                if escolha == "1":
                    numero = int(input("numero: ").strip())
                    nome = input("nome: ").strip()
                    partido = input("partido: ").strip() or "SEM PARTIDO"
                    candidato = cliente.urna.adicionar_candidato(numero, nome, partido)
                    print(f"  {candidato.nome} adicionado (aviso enviado por callback).")

                elif escolha == "2":
                    numero = int(input("numero: ").strip())
                    candidato = cliente.urna.remover_candidato(numero)
                    print(f"  {candidato.nome} removido.")

                elif escolha == "3":
                    print("  tipos: NOTIFICACAO | ALERTA | ATUALIZACAO")
                    tipo = input("  tipo: ").strip().upper() or "NOTIFICACAO"
                    mensagem = input("  mensagem: ").strip()
                    if mensagem:
                        total = cliente.painel.publicar(tipo, mensagem, cliente.nome)
                        print(f"  Nota entregue a {total} ouvinte(s).")

                elif escolha == "4":
                    for c in cliente.urna.listar_candidatos():
                        print(f"  {c.numero:>3} - {c.nome} ({c.partido}) — {c.votos} voto(s)")

                elif escolha == "5":
                    apuracao = cliente.urna.apurar()
                    for linha in apuracao["resultado"]:
                        print(f"  {linha['numero']:>3} {linha['nome']:<16} "
                              f"{linha['votos']:>3} voto(s)  {linha['percentual']}%")
                    vencedor = apuracao["vencedor"]
                    print("  vencedor:", vencedor["nome"] if vencedor else "—")

                elif escolha == "6":
                    print("  inscritos:", ", ".join(cliente.painel.inscritos()) or "(ninguem)")

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
