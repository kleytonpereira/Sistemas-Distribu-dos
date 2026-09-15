from __future__ import annotations

import socketserver
import threading
import time
import traceback
import xmlrpc.client
from typing import Any, Dict, Optional
from xmlrpc.server import SimpleXMLRPCServer

from comum.rmi.mensagem import desempacotar_valores, empacotar_valores
from comum.rmi.objeto_remoto import ObjetoRemoto
from comum.rmi.proxy import ProxyRemoto
from comum.rmi.referencia import RemoteObjectRef
from comum.rmi.transporte import METODO_DE_TRANSPORTE, getRequest, sendReply
from comum.rmi.transporte import Transporte

class ServidorXMLRPCConcorrente(socketserver.ThreadingMixIn, SimpleXMLRPCServer):
    daemon_threads = True
    allow_reuse_address = True

class ServidorRMI:
    def __init__(self, porta: int = 0, host: str = "127.0.0.1",
                 registrar_log: bool = True) -> None:
        self.host = host
        self._registrar_log = registrar_log

        self.instante = int(time.time())

        self._objetos: Dict[str, ObjetoRemoto] = {}
        self._referencias: Dict[int, RemoteObjectRef] = {}
        self._proximo_numero = 1
        self._trava = threading.Lock()

        self._http = ServidorXMLRPCConcorrente(
            (host, porta), allow_none=True, logRequests=False)
        self.porta = self._http.server_address[1]

        self._http.register_function(self._trocar, METODO_DE_TRANSPORTE)

        self._thread: Optional[threading.Thread] = None

    def registrar(self, nome: str, objeto: ObjetoRemoto) -> RemoteObjectRef:
        if not isinstance(objeto, ObjetoRemoto):
            raise TypeError(
                f"{type(objeto).__name__} nao herda de ObjetoRemoto, entao nao "
                f"pode ser publicado (passaria por valor, nao por referencia)."
            )

        with self._trava:
            referencia = RemoteObjectRef(
                endereco=self.host,
                porta=self.porta,
                instante=self.instante,
                numero_objeto=self._proximo_numero,
                interface=type(objeto).__name__,
                nome=nome,
            )
            self._proximo_numero += 1
            self._objetos[nome] = objeto
            self._referencias[id(objeto)] = referencia

        if self._registrar_log:
            print(f"[rmi] publicado {referencia}")
        return referencia

    def referencia_de(self, objeto: ObjetoRemoto) -> RemoteObjectRef:
        with self._trava:
            existente = self._referencias.get(id(objeto))
        if existente is not None:
            return existente

        nome = f"{type(objeto).__name__.lower()}#{self._proximo_numero}"
        return self.registrar(nome, objeto)

    def proxy_para(self, referencia: RemoteObjectRef) -> ProxyRemoto:
        return ProxyRemoto(referencia, Transporte(referencia.url))

    def _trocar(self, binario) -> xmlrpc.client.Binary:
        requisicao = getRequest(binario.data)

        if self._registrar_log:
            print(f"[rmi] <- {requisicao}")

        resultado = self._executar(requisicao.referencia_objeto,
                                   requisicao.id_metodo,
                                   requisicao.argumentos)

        return xmlrpc.client.Binary(sendReply(
            empacotar_valores(resultado),
            requisicao.id_requisicao,
            requisicao.referencia_objeto,
            requisicao.id_metodo,
        ))

    def _executar(self, nome_objeto: str, nome_metodo: str,
                  argumentos: bytes) -> Dict[str, Any]:

        try:
            objeto = self._objetos.get(nome_objeto)
            if objeto is None:
                raise LookupError(f"Objeto remoto '{nome_objeto}' nao encontrado.")
            if not objeto.pode_invocar(nome_metodo):
                raise AttributeError(
                    f"'{nome_metodo}' nao e' um metodo remoto de "
                    f"{type(objeto).__name__}."
                )

            pacote = desempacotar_valores(argumentos, criar_proxy=self.proxy_para)
            args = pacote.get("args", []) if isinstance(pacote, dict) else []
            kwargs = pacote.get("kwargs", {}) if isinstance(pacote, dict) else {}

            retorno = getattr(objeto, nome_metodo)(*args, **kwargs)

            return {"valor": self._preparar_retorno(retorno)}

        except Exception as erro:
            if self._registrar_log:
                print(f"[rmi] erro em {nome_objeto}.{nome_metodo}: {erro!r}")
                traceback.print_exc()
            return {"erro": True, "tipo": type(erro).__name__, "mensagem": str(erro)}

    def _preparar_retorno(self, valor: Any) -> Any:
        if isinstance(valor, ObjetoRemoto):
            return self.referencia_de(valor)
        if isinstance(valor, (list, tuple)):
            return [self._preparar_retorno(item) for item in valor]
        if isinstance(valor, dict):
            return {chave: self._preparar_retorno(item)
                    for chave, item in valor.items()}
        return valor

    def iniciar(self, anunciar: bool = True) -> None:
        if anunciar:
            print(f"[rmi] servidor em http://{self.host}:{self.porta}/")
        self._http.serve_forever()

    def iniciar_em_thread(self) -> threading.Thread:
        self._thread = threading.Thread(target=self._http.serve_forever, daemon=True)
        self._thread.start()
        return self._thread

    def parar(self) -> None:
        self._http.shutdown()
        self._http.server_close()

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.porta}/"
