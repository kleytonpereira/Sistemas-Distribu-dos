from __future__ import annotations

import io
import json
import struct
from typing import BinaryIO, Sequence

from comum.core.pojos import POJOSerializavel

ASSINATURA = b"POJO"
VERSAO_FORMATO = 1

_CABECALHO_LOTE = struct.Struct("!4sBI")
_TAM_TIPO = struct.Struct("!H")
_TAM_DADOS = struct.Struct("!I")

class CandidatoOutputStream(io.RawIOBase):
    def __init__(self,
                 destino: BinaryIO,
                 objetos: Sequence[POJOSerializavel],
                 quantidade: int) -> None:
        super().__init__()

        if not hasattr(destino, "write"):
            raise TypeError("O destino precisa ser um stream binario (ter .write).")
        if quantidade < 0:
            raise ValueError("quantidade nao pode ser negativa.")
        if quantidade > len(objetos):
            raise ValueError(
                f"Pedido para enviar {quantidade} objetos, mas o array tem {len(objetos)}."
            )

        self._destino = destino
        self._objetos = list(objetos)
        self._quantidade = quantidade
        self._bytes_escritos = 0

    def writable(self) -> bool:
        return True

    def write(self, dados) -> int:
        if self.closed:
            raise ValueError("Stream fechado.")
        quantidade = self._destino.write(bytes(dados))

        quantidade = len(dados) if quantidade is None else quantidade
        self._bytes_escritos += quantidade
        return quantidade

    def flush(self) -> None:
        if hasattr(self._destino, "flush"):
            self._destino.flush()

    def close(self) -> None:
        if not self.closed:
            self.flush()
        super().close()

    @staticmethod
    def _serializar_objeto(objeto: POJOSerializavel) -> bytes:
        dicionario = objeto.para_dicionario()

        nome_tipo = dicionario.pop("_tipo").encode("utf-8")
        dados_json = json.dumps(dicionario, ensure_ascii=False).encode("utf-8")

        return (_TAM_TIPO.pack(len(nome_tipo)) + nome_tipo
                + _TAM_DADOS.pack(len(dados_json)) + dados_json)

    def enviar(self) -> int:
        self.write(_CABECALHO_LOTE.pack(ASSINATURA, VERSAO_FORMATO, self._quantidade))

        for indice in range(self._quantidade):
            self.write(self._serializar_objeto(self._objetos[indice]))

        self.flush()
        return self._bytes_escritos

    @property
    def bytes_escritos(self) -> int:
        return self._bytes_escritos
