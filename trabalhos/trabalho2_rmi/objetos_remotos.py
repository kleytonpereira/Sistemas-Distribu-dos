from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional

from comum.core.pojos import (
    Administrador,
    Candidato,
    Eleitor,
    NotaInformativa,
    TIPOS_DE_NOTA,
)
from comum.core.servicos import ErroDeServico, ServicoAutenticacao, ServicoVotacao
from comum.rmi import ObjetoRemoto, metodo_remoto

class ServicoAutenticacaoRemoto(ObjetoRemoto):
    def __init__(self, servico: ServicoAutenticacao,
                 votacao: "ServicoVotacaoRemoto") -> None:
        self._servico = servico
        self._votacao = votacao
        self._sessoes: Dict[str, "SessaoEleitor"] = {}
        self._trava = threading.Lock()

    @metodo_remoto
    def login(self, login: str, senha: str) -> "SessaoEleitor":
        pessoa = self._servico.autenticar(login, senha)

        with self._trava:
            sessao = self._sessoes.get(login)
            if sessao is None:
                sessao = SessaoEleitor(pessoa, self._votacao)
                self._sessoes[login] = sessao
        return sessao

    @metodo_remoto
    def quem_esta_logado(self) -> List[str]:
        with self._trava:
            return sorted(self._sessoes)

class ServicoVotacaoRemoto(ObjetoRemoto):
    def __init__(self, servico: ServicoVotacao,
                 painel: Optional["PainelDeNotas"] = None) -> None:
        self._servico = servico
        self._painel = painel

    def ligar_painel(self, painel: "PainelDeNotas") -> None:
        self._painel = painel

    @metodo_remoto
    def listar_candidatos(self) -> List[Candidato]:
        return self._servico.listar_candidatos()

    @metodo_remoto
    def segundos_restantes(self) -> int:
        return self._servico.segundos_restantes()

    @metodo_remoto
    def apurar(self) -> Dict[str, Any]:
        return self._servico.apurar()

    @metodo_remoto
    def adicionar_candidato(self, numero: int, nome: str,
                            partido: str = "SEM PARTIDO") -> Candidato:

        candidato = Candidato(numero=int(numero), nome=nome, partido=partido)
        self._servico.adicionar_candidato(candidato)
        if self._painel is not None:
            self._painel.publicar("ATUALIZACAO",
                                  f"Novo candidato: {candidato.numero} - {candidato.nome}")
        return candidato

    @metodo_remoto
    def remover_candidato(self, numero: int) -> Candidato:
        candidato = self._servico.remover_candidato(int(numero))
        if self._painel is not None:
            self._painel.publicar("ATUALIZACAO",
                                  f"Candidato removido: {candidato.numero} - {candidato.nome}")
        return candidato

    def servico(self) -> ServicoVotacao:
        return self._servico

class SessaoEleitor(ObjetoRemoto):
    def __init__(self, pessoa, votacao: ServicoVotacaoRemoto) -> None:
        self._pessoa = pessoa
        self._votacao = votacao

    @metodo_remoto
    def quem_sou(self):
        return self._pessoa

    @metodo_remoto
    def e_administrador(self) -> bool:
        return isinstance(self._pessoa, Administrador)

    @metodo_remoto
    def votar(self, numero_candidato: int):
        if not isinstance(self._pessoa, Eleitor):
            raise ErroDeServico("Administradores nao votam.")
        return self._votacao.servico().registrar_voto(self._pessoa,
                                                      int(numero_candidato))

    @metodo_remoto
    def ja_votei(self) -> bool:
        return bool(getattr(self._pessoa, "ja_votou", False))

    @metodo_remoto
    def urna(self) -> ServicoVotacaoRemoto:
        return self._votacao

class PainelDeNotas(ObjetoRemoto):
    def __init__(self) -> None:
        self._receptores: Dict[str, Any] = {}
        self._historico: List[NotaInformativa] = []
        self._trava = threading.Lock()

    @metodo_remoto
    def registrar_receptor(self, nome: str, receptor) -> int:
        with self._trava:
            self._receptores[nome] = receptor
            total = len(self._receptores)
        print(f"[painel] {nome} inscrito ({total} ouvinte(s))")
        self.publicar("NOTIFICACAO", f"{nome} entrou.")
        return total

    @metodo_remoto
    def cancelar_receptor(self, nome: str) -> int:
        with self._trava:
            self._receptores.pop(nome, None)
            total = len(self._receptores)
        print(f"[painel] {nome} saiu ({total} ouvinte(s))")
        return total

    @metodo_remoto
    def inscritos(self) -> List[str]:
        with self._trava:
            return sorted(self._receptores)

    @metodo_remoto
    def historico(self) -> List[NotaInformativa]:
        with self._trava:
            return list(self._historico)

    @metodo_remoto
    def publicar(self, tipo: str, mensagem: str, autor: str = "SISTEMA") -> int:
        if tipo not in TIPOS_DE_NOTA:
            raise ErroDeServico(f"Tipo invalido. Use um de {TIPOS_DE_NOTA}.")

        nota = NotaInformativa(tipo=tipo, mensagem=f"[{autor}] {mensagem}")
        with self._trava:
            self._historico.append(nota)
            destinos = list(self._receptores.items())

        for nome, receptor in destinos:
            threading.Thread(target=self._entregar, args=(nome, receptor, nota),
                             daemon=True).start()

        print(f"[painel] {tipo} ({autor}): {mensagem} -> {len(destinos)} ouvinte(s)")
        return len(destinos)

    def _entregar(self, nome: str, receptor, nota: NotaInformativa) -> None:
        try:
            receptor.receber_nota(nota)
        except Exception as erro:
            print(f"[painel] {nome} inalcancavel ({erro}); removendo da lista")
            with self._trava:
                self._receptores.pop(nome, None)
