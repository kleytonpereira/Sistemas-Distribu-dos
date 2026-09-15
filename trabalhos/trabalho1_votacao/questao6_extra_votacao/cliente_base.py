from __future__ import annotations

from trabalho1_votacao.questao6_extra_votacao.configuracao import PORTA_TCP
from comum.sockets import ClienteTCP, ErroRemoto, OuvinteMulticast
from comum.sockets.multicast import formatar_nota

HOST_SERVIDOR = "127.0.0.1"

class ClienteVotacao(ClienteTCP):
    def __init__(self, login: str, senha: str,
                 host: str = HOST_SERVIDOR, porta: int = PORTA_TCP) -> None:
        super().__init__(host, porta)
        self._login = login
        self._senha = senha
        self._ouvinte: OuvinteMulticast | None = None
        self.perfil = ""
        self.nome = ""

    def entrar(self) -> bool:
        try:
            dados = self.chamar("LOGIN", login=self._login, senha=self._senha)
        except ErroRemoto as erro:
            print("Falha no login:", erro)
            return False

        self.nome = dados["nome"]
        self.perfil = dados["perfil"]
        print(f"Logado como {self.nome} ({self.perfil}).")
        print(f"Prazo restante da votacao: {dados['segundos_restantes']}s")
        print("\nCandidatos recebidos junto com o login:")
        for candidato in dados["candidatos"]:
            print(f"  {candidato['numero']:>3} - {candidato['nome']} "
                  f"({candidato['partido']})")

        self._ouvinte = OuvinteMulticast(dados["grupo_multicast"],
                                         dados["porta_multicast"],
                                         self._exibir_nota)
        if self._ouvinte.entrar():
            self._ouvinte.iniciar()
            print(f"\nEscutando notas em {dados['grupo_multicast']}:"
                  f"{dados['porta_multicast']}.\n")
        else:

            self._ouvinte = None
        return True

    @staticmethod
    def _exibir_nota(nota, remetente) -> None:
        print(f"\n  >>> {formatar_nota(nota)}\n> ", end="", flush=True)

    def sair(self) -> None:
        if self._ouvinte is not None:
            self._ouvinte.sair()
        self.fechar()
        print("Cliente encerrado.")
