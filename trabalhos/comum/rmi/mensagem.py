from __future__ import annotations

import json
import struct
from dataclasses import dataclass
from typing import Any, Callable, Optional

from comum.core.pojos import POJOSerializavel
from comum.rmi.referencia import RemoteObjectRef

TIPO_REQUISICAO = 0
TIPO_RESPOSTA = 1

_CABECALHO = struct.Struct("!BI")
_TAM_CURTO = struct.Struct("!H")
_TAM_LONGO = struct.Struct("!I")

@dataclass
class Mensagem:
    tipo: int
    id_requisicao: int
    referencia_objeto: str
    id_metodo: str
    argumentos: bytes

    def empacotar(self) -> bytes:
        referencia = self.referencia_objeto.encode("utf-8")
        metodo = self.id_metodo.encode("utf-8")
        return (
            _CABECALHO.pack(self.tipo, self.id_requisicao)
            + _TAM_CURTO.pack(len(referencia)) + referencia
            + _TAM_CURTO.pack(len(metodo)) + metodo
            + _TAM_LONGO.pack(len(self.argumentos)) + self.argumentos
        )

    @staticmethod
    def desempacotar(dados: bytes) -> "Mensagem":
        posicao = 0

        tipo, id_requisicao = _CABECALHO.unpack_from(dados, posicao)
        posicao += _CABECALHO.size

        (tamanho,) = _TAM_CURTO.unpack_from(dados, posicao)
        posicao += _TAM_CURTO.size
        referencia = dados[posicao:posicao + tamanho].decode("utf-8")
        posicao += tamanho

        (tamanho,) = _TAM_CURTO.unpack_from(dados, posicao)
        posicao += _TAM_CURTO.size
        metodo = dados[posicao:posicao + tamanho].decode("utf-8")
        posicao += tamanho

        (tamanho,) = _TAM_LONGO.unpack_from(dados, posicao)
        posicao += _TAM_LONGO.size
        argumentos = dados[posicao:posicao + tamanho]

        return Mensagem(tipo=tipo, id_requisicao=id_requisicao,
                        referencia_objeto=referencia, id_metodo=metodo,
                        argumentos=argumentos)

    def __str__(self) -> str:
        nome_tipo = "REQUISICAO" if self.tipo == TIPO_REQUISICAO else "RESPOSTA"
        return (f"{nome_tipo} #{self.id_requisicao} "
                f"{self.referencia_objeto}.{self.id_metodo} "
                f"({len(self.argumentos)} bytes de argumentos)")

def _converter_para_json(valor: Any) -> Any:
    if isinstance(valor, RemoteObjectRef):
        return valor.para_dicionario()
    if isinstance(valor, POJOSerializavel):
        return valor.para_dicionario()
    if isinstance(valor, dict):
        return {chave: _converter_para_json(item) for chave, item in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [_converter_para_json(item) for item in valor]
    return valor

def _converter_de_json(valor: Any, criar_proxy: Optional[Callable]) -> Any:
    if RemoteObjectRef.e_referencia(valor):
        referencia = RemoteObjectRef.de_dicionario(valor)
        return criar_proxy(referencia) if criar_proxy else referencia
    if isinstance(valor, dict):
        if "_tipo" in valor:
            return POJOSerializavel.de_dicionario(valor)
        return {chave: _converter_de_json(item, criar_proxy)
                for chave, item in valor.items()}
    if isinstance(valor, list):
        return [_converter_de_json(item, criar_proxy) for item in valor]
    return valor

def empacotar_valores(valores: Any) -> bytes:
    return json.dumps(_converter_para_json(valores), ensure_ascii=False).encode("utf-8")

def desempacotar_valores(dados: bytes, criar_proxy: Optional[Callable] = None) -> Any:
    if not dados:
        return None
    return _converter_de_json(json.loads(dados.decode("utf-8")), criar_proxy)
