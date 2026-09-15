from __future__ import annotations

import threading
import time
from typing import Dict, List, Optional

from .pojos import Administrador, Candidato, Eleitor, Voto

class ErroDeServico(Exception):
    pass

class ServicoAutenticacao:
    def __init__(self) -> None:
        self._trava = threading.RLock()
        self._eleitores: Dict[str, Eleitor] = {}
        self._administradores: Dict[str, Administrador] = {}

    def cadastrar_eleitor(self, eleitor: Eleitor) -> Eleitor:
        with self._trava:
            if eleitor.login in self._eleitores:
                raise ErroDeServico(f"Eleitor '{eleitor.login}' ja cadastrado.")
            self._eleitores[eleitor.login] = eleitor
            return eleitor

    def cadastrar_administrador(self, admin: Administrador) -> Administrador:
        with self._trava:
            self._administradores[admin.login] = admin
            return admin

    def autenticar(self, login: str, senha: str):
        with self._trava:
            pessoa = self._eleitores.get(login) or self._administradores.get(login)
            if pessoa is None or pessoa.senha != senha:
                raise ErroDeServico("Login ou senha invalidos.")
            return pessoa

    def buscar_eleitor(self, login: str) -> Optional[Eleitor]:
        with self._trava:
            return self._eleitores.get(login)

class ServicoVotacao:
    def __init__(self, duracao_segundos: int = 300) -> None:
        self._trava = threading.RLock()
        self._candidatos: Dict[int, Candidato] = {}
        self._votos: List[Voto] = []
        self._instante_inicio = time.time()
        self._duracao = duracao_segundos

    def segundos_restantes(self) -> int:
        restante = self._duracao - (time.time() - self._instante_inicio)
        return max(0, int(restante))

    def votacao_encerrada(self) -> bool:
        return self.segundos_restantes() <= 0

    def reiniciar_prazo(self, duracao_segundos: int) -> None:
        with self._trava:
            self._instante_inicio = time.time()
            self._duracao = duracao_segundos

    def adicionar_candidato(self, candidato: Candidato) -> Candidato:
        with self._trava:
            if candidato.numero in self._candidatos:
                raise ErroDeServico(f"Ja existe candidato com numero {candidato.numero}.")
            self._candidatos[candidato.numero] = candidato
            return candidato

    def remover_candidato(self, numero: int) -> Candidato:
        with self._trava:
            candidato = self._candidatos.pop(numero, None)
            if candidato is None:
                raise ErroDeServico(f"Candidato {numero} nao encontrado.")
            return candidato

    def listar_candidatos(self) -> List[Candidato]:
        with self._trava:

            return sorted(self._candidatos.values(), key=lambda c: c.numero)

    def registrar_voto(self, eleitor: Eleitor, numero_candidato: int) -> Voto:
        with self._trava:
            if self.votacao_encerrada():
                raise ErroDeServico("Prazo encerrado: a urna nao aceita mais votos.")
            candidato = self._candidatos.get(numero_candidato)
            if candidato is None:
                raise ErroDeServico(f"Candidato {numero_candidato} nao existe.")
            if eleitor.ja_votou:
                raise ErroDeServico("Este eleitor ja votou.")

            voto = Voto(titulo_eleitor=eleitor.titulo, numero_candidato=numero_candidato)
            self._votos.append(voto)
            candidato.votos += 1
            eleitor.ja_votou = True
            return voto

    def apurar(self) -> dict:
        with self._trava:
            total = len(self._votos)
            resultado = []
            for candidato in self.listar_candidatos():

                percentual = (candidato.votos / total * 100) if total else 0.0
                resultado.append({
                    "numero": candidato.numero,
                    "nome": candidato.nome,
                    "partido": candidato.partido,
                    "votos": candidato.votos,
                    "percentual": round(percentual, 2),
                })

            vencedor = max(resultado, key=lambda r: r["votos"], default=None)
            if vencedor is not None and vencedor["votos"] == 0:
                vencedor = None

            return {
                "total_de_votos": total,
                "encerrada": self.votacao_encerrada(),
                "resultado": resultado,
                "vencedor": vencedor,
            }

def candidatos_de_exemplo() -> List[Candidato]:
    return [
        Candidato(numero=13, nome="Ana Ribeiro",   partido="PARTIDO A"),
        Candidato(numero=22, nome="Bruno Castro",  partido="PARTIDO B"),
        Candidato(numero=45, nome="Carla Menezes", partido="PARTIDO C"),
        Candidato(numero=99, nome="Voto Nulo",     partido="-"),
    ]

def eleitores_de_exemplo() -> List[Eleitor]:
    return [
        Eleitor(nome="Kleyton",  login="kleyton", senha="123", titulo="0001"),
        Eleitor(nome="Mariana",  login="mariana", senha="123", titulo="0002"),
        Eleitor(nome="Joao",     login="joao",    senha="123", titulo="0003"),
    ]

def administradores_de_exemplo() -> List[Administrador]:
    return [
        Administrador(nome="Prof. Rafael", login="admin", senha="admin", matricula="A001"),
    ]
