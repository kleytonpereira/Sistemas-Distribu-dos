from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

MARCADOR = "_ref"

@dataclass(frozen=True)
class RemoteObjectRef:
    endereco: str
    porta: int
    instante: int
    numero_objeto: int
    interface: str
    nome: str

    @property
    def url(self) -> str:
        return f"http://{self.endereco}:{self.porta}/"

    def para_dicionario(self) -> Dict[str, Any]:
        return {
            MARCADOR: True,
            "endereco": self.endereco,
            "porta": self.porta,
            "instante": self.instante,
            "numero_objeto": self.numero_objeto,
            "interface": self.interface,
            "nome": self.nome,
        }

    @staticmethod
    def de_dicionario(dados: Dict[str, Any]) -> "RemoteObjectRef":
        return RemoteObjectRef(
            endereco=dados["endereco"],
            porta=dados["porta"],
            instante=dados["instante"],
            numero_objeto=dados["numero_objeto"],
            interface=dados["interface"],
            nome=dados["nome"],
        )

    @staticmethod
    def e_referencia(dados: Any) -> bool:
        return isinstance(dados, dict) and dados.get(MARCADOR) is True

    def __str__(self) -> str:
        return f"<{self.interface} '{self.nome}' em {self.endereco}:{self.porta}>"
