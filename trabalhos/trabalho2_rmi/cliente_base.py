from __future__ import annotations

import time
from typing import Optional

from comum.core.pojos import NotaInformativa
from comum.rmi import (
    ErroRemotoRMI,
    ObjetoRemoto,
    ProxyRemoto,
    RemoteObjectRef,
    ServidorRMI,
    Transporte,
    metodo_remoto,
)
from trabalho2_rmi.configuracao import HOST_SERVIDOR, PORTA_SERVIDOR

class ReceptorDeNotas(ObjetoRemoto):
    def __init__(self, ao_receber=None) -> None:
        self._ao_receber = ao_receber
        self.recebidas = []

    @metodo_remoto
    def receber_nota(self, nota: NotaInformativa) -> bool:
        self.recebidas.append(nota)
        if self._ao_receber:
            self._ao_receber(nota)
        return True

def formatar(nota: NotaInformativa) -> str:
    instante = time.strftime("%H:%M:%S", time.localtime(nota.timestamp))
    return f"[{instante}] <{nota.tipo}> {nota.mensagem}"

class ClienteRMI:
    def __init__(self, login: str, senha: str,
                 host: str = HOST_SERVIDOR, porta: int = PORTA_SERVIDOR) -> None:
        self._login = login
        self._senha = senha
        self._transporte = Transporte(f"http://{host}:{porta}/")

        self.sessao: Optional[ProxyRemoto] = None
        self.urna: Optional[ProxyRemoto] = None
        self.painel: Optional[ProxyRemoto] = None
        self.nome = ""
        self.e_admin = False

        self._meu_servidor: Optional[ServidorRMI] = None
        self._receptor: Optional[ReceptorDeNotas] = None

    def _proxy(self, nome_objeto: str) -> ProxyRemoto:
        referencia = RemoteObjectRef(
            endereco=self._transporte.url.split("//")[1].split(":")[0],
            porta=int(self._transporte.url.rstrip("/").split(":")[-1]),
            instante=0,
            numero_objeto=0,
            interface="?",
            nome=nome_objeto,
        )
        return ProxyRemoto(referencia, self._transporte)

    def entrar(self) -> bool:
        auth = self._proxy("auth")
        try:

            self.sessao = auth.login(self._login, self._senha)
        except ErroRemotoRMI as erro:
            print("Falha no login:", erro.mensagem)
            return False

        pessoa = self.sessao.quem_sou()
        self.nome = pessoa.nome
        self.e_admin = self.sessao.e_administrador()

        self.urna = self.sessao.urna()
        self.painel = self._proxy("painel")

        print(f"Logado como {self.nome} ({'ADMIN' if self.e_admin else 'ELEITOR'}).")
        print(f"Prazo restante: {self.urna.segundos_restantes()}s")
        print("\nCandidatos (chegaram por VALOR, sao copias):")
        for candidato in self.urna.listar_candidatos():
            print(f"  {candidato.numero:>3} - {candidato.nome} ({candidato.partido})")

        self._inscrever_no_painel()
        return True

    def _inscrever_no_painel(self) -> None:
        self._receptor = ReceptorDeNotas(
            ao_receber=lambda nota: print(f"\n  >>> {formatar(nota)}\n> ",
                                          end="", flush=True))

        self._meu_servidor = ServidorRMI(porta=0, registrar_log=False)
        referencia = self._meu_servidor.registrar(f"receptor-{self._login}",
                                                  self._receptor)
        self._meu_servidor.iniciar_em_thread()

        self.painel.registrar_receptor(self._login, referencia)
        print(f"\nInscrito no painel de notas (meu servidor: {self._meu_servidor.url}).\n")

    def sair(self) -> None:
        try:
            if self.painel is not None:
                self.painel.cancelar_receptor(self._login)
        except Exception:
            pass
        if self._meu_servidor is not None:
            self._meu_servidor.parar()
        print("Cliente encerrado.")
