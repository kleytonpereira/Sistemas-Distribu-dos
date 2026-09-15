from __future__ import annotations

import itertools
import threading
import xmlrpc.client
from typing import Optional

from comum.rmi.mensagem import TIPO_REQUISICAO, TIPO_RESPOSTA, Mensagem
from comum.rmi.referencia import RemoteObjectRef

METODO_DE_TRANSPORTE = "trocar"

class Transporte:
    def __init__(self, url: str) -> None:
        self.url = url

        self._local = threading.local()

        self._contador = itertools.count(1)
        self._trava = threading.Lock()

    @property
    def _rpc(self) -> xmlrpc.client.ServerProxy:
        proxy = getattr(self._local, "proxy", None)
        if proxy is None:

            proxy = xmlrpc.client.ServerProxy(self.url, allow_none=True)
            self._local.proxy = proxy
        return proxy

    def _proximo_id(self) -> int:
        with self._trava:
            return next(self._contador)

    def doOperation(self, objeto: RemoteObjectRef, id_metodo: str,
                    argumentos: bytes) -> bytes:

        requisicao = Mensagem(
            tipo=TIPO_REQUISICAO,
            id_requisicao=self._proximo_id(),
            referencia_objeto=objeto.nome,
            id_metodo=id_metodo,
            argumentos=argumentos,
        )

        metodo_rpc = getattr(self._rpc, METODO_DE_TRANSPORTE)
        retorno = metodo_rpc(xmlrpc.client.Binary(requisicao.empacotar()))

        resposta = Mensagem.desempacotar(retorno.data)

        if resposta.id_requisicao != requisicao.id_requisicao:
            raise RuntimeError(
                f"Resposta fora de ordem: esperava #{requisicao.id_requisicao}, "
                f"veio #{resposta.id_requisicao}"
            )
        if resposta.tipo != TIPO_RESPOSTA:
            raise RuntimeError(f"Esperava uma RESPOSTA, veio tipo {resposta.tipo}")

        return resposta.argumentos

def getRequest(dados: bytes) -> Mensagem:
    requisicao = Mensagem.desempacotar(dados)
    if requisicao.tipo != TIPO_REQUISICAO:
        raise ValueError(f"Esperava uma REQUISICAO, veio tipo {requisicao.tipo}")
    return requisicao

def sendReply(resposta_empacotada: bytes, id_requisicao: int,
              referencia_objeto: str, id_metodo: str) -> bytes:

    return Mensagem(
        tipo=TIPO_RESPOSTA,
        id_requisicao=id_requisicao,
        referencia_objeto=referencia_objeto,
        id_metodo=id_metodo,
        argumentos=resposta_empacotada,
    ).empacotar()
