from __future__ import annotations

from typing import Any

from comum.rmi.mensagem import desempacotar_valores, empacotar_valores
from comum.rmi.referencia import RemoteObjectRef
from comum.rmi.transporte import Transporte

class ErroRemotoRMI(Exception):
    def __init__(self, tipo: str, mensagem: str) -> None:
        super().__init__(f"{tipo}: {mensagem}")
        self.tipo = tipo
        self.mensagem = mensagem

class ProxyRemoto:
    def __init__(self, referencia: RemoteObjectRef, transporte: Transporte) -> None:
        object.__setattr__(self, "_referencia", referencia)
        object.__setattr__(self, "_transporte", transporte)

    @property
    def referencia(self) -> RemoteObjectRef:
        return object.__getattribute__(self, "_referencia")

    def _criar_proxy(self, referencia: RemoteObjectRef) -> "ProxyRemoto":
        transporte = object.__getattribute__(self, "_transporte")
        if referencia.url != transporte.url:
            transporte = Transporte(referencia.url)
        return ProxyRemoto(referencia, transporte)

    def _invocar(self, id_metodo: str, *args: Any, **kwargs: Any) -> Any:
        referencia = object.__getattribute__(self, "_referencia")
        transporte = object.__getattribute__(self, "_transporte")

        argumentos = empacotar_valores({"args": list(args), "kwargs": kwargs})

        bruto = transporte.doOperation(referencia, id_metodo, argumentos)

        resposta = desempacotar_valores(bruto, criar_proxy=self._criar_proxy)

        if isinstance(resposta, dict) and resposta.get("erro"):
            raise ErroRemotoRMI(resposta["tipo"], resposta["mensagem"])
        return resposta.get("valor") if isinstance(resposta, dict) else resposta

    def __getattr__(self, nome: str):
        if nome.startswith("_"):

            raise AttributeError(nome)

        def chamada_remota(*args, **kwargs):
            return self._invocar(nome, *args, **kwargs)

        chamada_remota.__name__ = nome
        return chamada_remota

    def __repr__(self) -> str:
        return f"ProxyRemoto({object.__getattribute__(self, '_referencia')})"
