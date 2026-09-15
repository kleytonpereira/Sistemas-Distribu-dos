import sys

from trabalho1_votacao.questao6_extra_votacao.cliente_base import ClienteVotacao

MENU = """
[1] adicionar candidato   [2] remover candidato   [3] enviar nota informativa
[4] listar candidatos     [5] apuracao            [0] sair"""

def main() -> None:
    login = sys.argv[1] if len(sys.argv) > 1 else "admin"
    senha = sys.argv[2] if len(sys.argv) > 2 else "admin"

    cliente = ClienteVotacao(login, senha)
    try:
        if not cliente.entrar():
            return
        if cliente.perfil != "ADMIN":
            print("Este cliente e' so' para administradores.")
            return

        while True:
            print(MENU)
            escolha = input("> ").strip()

            if escolha == "1":
                try:
                    numero = int(input("numero: ").strip())
                except ValueError:
                    print("  numero invalido.")
                    continue
                if cliente.tentar("ADICIONAR_CANDIDATO", numero=numero,
                                  nome=input("nome: ").strip(),
                                  partido=input("partido: ").strip() or "SEM PARTIDO"):
                    print("  Candidato adicionado (aviso enviado por multicast).")

            elif escolha == "2":
                try:
                    numero = int(input("numero: ").strip())
                except ValueError:
                    print("  numero invalido.")
                    continue
                if cliente.tentar("REMOVER_CANDIDATO", numero=numero):
                    print("  Candidato removido (aviso enviado por multicast).")

            elif escolha == "3":
                print("  tipos: NOTIFICACAO | ALERTA | ATUALIZACAO")
                tipo = input("  tipo: ").strip().upper() or "NOTIFICACAO"
                mensagem = input("  mensagem: ").strip()
                if mensagem and cliente.tentar("ENVIAR_NOTA", tipo=tipo,
                                               mensagem=mensagem):
                    print("  Nota publicada no grupo multicast.")

            elif escolha == "4":
                dados = cliente.tentar("LISTAR_CANDIDATOS")
                if dados:
                    for candidato in dados["candidatos"]:
                        print(f"  {candidato['numero']:>3} - {candidato['nome']} "
                              f"({candidato['partido']}) — {candidato['votos']} voto(s)")

            elif escolha == "5":
                dados = cliente.tentar("APURAR")
                if dados:
                    for linha in dados["resultado"]:
                        print(f"  {linha['numero']:>3} {linha['nome']:<16} "
                              f"{linha['votos']:>3} voto(s)  {linha['percentual']}%")
                    vencedor = dados["vencedor"]
                    print("  vencedor:", vencedor["nome"] if vencedor else "—")

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
