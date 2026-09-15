from __future__ import annotations

from typing import Callable, Set, TypeVar

F = TypeVar("F", bound=Callable)

_MARCA = "_e_metodo_remoto"

def metodo_remoto(funcao: F) -> F:
    setattr(funcao, _MARCA, True)
    return funcao

class ObjetoRemoto:
    @classmethod
    def metodos_remotos(cls) -> Set[str]:
        nomes = set()

        for nome in dir(cls):
            if nome.startswith("_"):
                continue
            atributo = getattr(cls, nome, None)
            if callable(atributo) and getattr(atributo, _MARCA, False):
                nomes.add(nome)
        return nomes

    def pode_invocar(self, nome_metodo: str) -> bool:
        return nome_metodo in type(self).metodos_remotos()
