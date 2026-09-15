import sys

from comum.sockets import ClienteTCP, ErroRemoto

HOST = "127.0.0.1"
PORTA = 5003

class ClienteVotacao(ClienteTCP):
    def __init__(self, host: str = HOST, porta: int = PORTA) -> None:
        super().__init__(host, porta)

    def listar_candidatos(self) -> dict:
        return self.chamar("LISTAR_CANDIDATOS")

    def login(self, login: str, senha: str) -> dict:
        return self.chamar("LOGIN", login=login, senha=senha)

    def votar(self, login: str, numero_candidato: int) -> dict:
        return self.chamar("VOTAR", login=login, numero_candidato=numero_candidato)

    def adicionar_candidato(self, numero: int, nome: str, partido: str) -> dict:
        return self.chamar("ADICIONAR_CANDIDATO",
                           numero=numero, nome=nome, partido=partido)

    def apurar(self) -> dict:
        return self.chamar("APURAR")

def demonstracao() -> None:
    print("=== Questao 3 — serializacao sobre sockets TCP ===\n")

    with ClienteVotacao() as cliente:
        print("1) LOGIN como eleitor 'kleyton'")
        resposta = cliente.login("kleyton", "123")
        print("   perfil:", resposta["perfil"], "| nome:", resposta["pessoa"]["nome"])

        print("\n2) LISTAR_CANDIDATOS")
        dados = cliente.listar_candidatos()
        for candidato in dados["candidatos"]:
            print(f"   {candidato['numero']:>3} - {candidato['nome']} "
                  f"({candidato['partido']})")
        print(f"   prazo restante: {dados['segundos_restantes']}s")

        print("\n3) VOTAR no candidato 13")
        print("   voto registrado:", cliente.votar("kleyton", 13)["voto"])

        print("\n4) VOTAR de novo (deve ser recusado pela regra de negocio)")
        try:
            cliente.votar("kleyton", 22)
        except ErroRemoto as erro:
            print("   recusado corretamente ->", erro)

        print("\n5) APURAR")
        apuracao = cliente.apurar()
        for linha in apuracao["resultado"]:
            print(f"   {linha['numero']:>3} {linha['nome']:<15} "
                  f"{linha['votos']} voto(s)  {linha['percentual']}%")
        vencedor = apuracao["vencedor"]
        print("   vencedor:", vencedor["nome"] if vencedor else "—")

def interativo() -> None:
    with ClienteVotacao() as cliente:
        login = input("login: ").strip()
        senha = input("senha: ").strip()
        try:
            perfil = cliente.login(login, senha)["perfil"]
        except ErroRemoto as erro:
            print("Falha no login:", erro)
            return
        print(f"Bem-vindo! Perfil: {perfil}\n")

        while True:
            print("[1] listar candidatos  [2] votar  [3] apurar  "
                  "[4] adicionar candidato  [0] sair")
            escolha = input("> ").strip()
            try:
                if escolha == "1":
                    for c in cliente.listar_candidatos()["candidatos"]:
                        print(f"  {c['numero']:>3} - {c['nome']} ({c['partido']})")
                elif escolha == "2":
                    print("  ok:", cliente.votar(login, int(input("numero: ")))["voto"])
                elif escolha == "3":
                    print("  ", cliente.apurar())
                elif escolha == "4":
                    print("  ok:", cliente.adicionar_candidato(
                        int(input("numero: ")), input("nome: "), input("partido: ")))
                elif escolha == "0":
                    break
                else:
                    print("  opcao invalida")
            except (ErroRemoto, ValueError) as erro:
                print("  erro:", erro)
            print()

if __name__ == "__main__":
    try:
        interativo() if "--interativo" in sys.argv else demonstracao()
    except ConnectionRefusedError:
        print("Nao consegui conectar. O servidor esta' rodando?")
        print("  python3 -m trabalho1_votacao.questao3_serializacao.servidor")
