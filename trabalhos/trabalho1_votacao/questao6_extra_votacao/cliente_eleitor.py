import sys

from trabalho1_votacao.questao6_extra_votacao.cliente_base import ClienteVotacao

MENU = """
[1] listar candidatos   [2] votar   [3] ver apuracao parcial   [0] sair"""

def main() -> None:
    login = sys.argv[1] if len(sys.argv) > 1 else "kleyton"
    senha = sys.argv[2] if len(sys.argv) > 2 else "123"

    cliente = ClienteVotacao(login, senha)
    try:
        if not cliente.entrar():
            return
        if cliente.perfil != "ELEITOR":
            print("Este cliente e' so' para eleitores. Use o cliente_admin.")
            return

        while True:
            print(MENU)
            escolha = input("> ").strip()

            if escolha == "1":
                dados = cliente.tentar("LISTAR_CANDIDATOS")
                if dados:
                    for candidato in dados["candidatos"]:
                        print(f"  {candidato['numero']:>3} - {candidato['nome']} "
                              f"({candidato['partido']})")
                    print(f"  prazo restante: {dados['segundos_restantes']}s")

            elif escolha == "2":
                try:
                    numero = int(input("numero do candidato: ").strip())
                except ValueError:
                    print("  numero invalido.")
                    continue
                if cliente.tentar("VOTAR", numero_candidato=numero):
                    print(f"  Voto registrado em {numero}. Obrigado!")

            elif escolha == "3":
                dados = cliente.tentar("APURAR")
                if dados:
                    for linha in dados["resultado"]:
                        print(f"  {linha['numero']:>3} {linha['nome']:<16} "
                              f"{linha['votos']:>3} voto(s)  {linha['percentual']}%")
                    print(f"  total: {dados['total_de_votos']} | "
                          f"encerrada: {'sim' if dados['encerrada'] else 'nao'}")

            elif escolha == "0":
                break
            else:
                print("  opcao invalida.")

    except (EOFError, KeyboardInterrupt):
        pass
    except ConnectionRefusedError:
        print("Servidor fora do ar. Rode: python3 -m trabalho1_votacao.questao6_extra_votacao.servidor")
        return
    finally:
        cliente.sair()

if __name__ == "__main__":
    main()
