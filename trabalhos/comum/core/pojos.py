from __future__ import annotations

import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict

class POJOSerializavel:
    _REGISTRO: Dict[str, type] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        POJOSerializavel._REGISTRO[cls.__name__] = cls

    def para_dicionario(self) -> Dict[str, Any]:
        dados = asdict(self)
        dados["_tipo"] = type(self).__name__
        return dados

    @staticmethod
    def de_dicionario(dados: Dict[str, Any]) -> "POJOSerializavel":
        dados = dict(dados)
        nome_tipo = dados.pop("_tipo", None)
        if nome_tipo is None:
            raise ValueError("Dicionario sem o campo '_tipo'; nao da' para saber a classe.")
        classe = POJOSerializavel._REGISTRO.get(nome_tipo)
        if classe is None:
            raise ValueError(f"Tipo desconhecido recebido: {nome_tipo!r}")
        return classe(**dados)

@dataclass
class Pessoa(POJOSerializavel):
    nome: str
    login: str
    senha: str

@dataclass
class Eleitor(Pessoa):
    titulo: str = ""
    ja_votou: bool = False

@dataclass
class Administrador(Pessoa):
    matricula: str = ""

@dataclass
class Candidato(POJOSerializavel):
    numero: int
    nome: str
    partido: str = "SEM PARTIDO"
    votos: int = 0

@dataclass
class Voto(POJOSerializavel):
    titulo_eleitor: str
    numero_candidato: int

    timestamp: int = field(default_factory=lambda: int(time.time()))

@dataclass
class NotaInformativa(POJOSerializavel):
    tipo: str
    mensagem: str
    timestamp: int = field(default_factory=lambda: int(time.time()))

TIPOS_DE_NOTA = ("NOTIFICACAO", "ALERTA", "ATUALIZACAO")
