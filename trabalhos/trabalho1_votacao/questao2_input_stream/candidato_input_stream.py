from __future__ import annotations

import io
import json
import struct
from typing import BinaryIO, List

from comum.core.pojos import POJOSerializavel
from trabalho1_votacao.questao1_output_stream.candidato_output_stream import (
    ASSINATURA,
    VERSAO_FORMATO,
    _CABECALHO_LOTE,
    _TAM_DADOS,
    _TAM_TIPO,
)

class FormatoInvalido(Exception):
    pass

class CandidatoInputStream(io.RawIOBase):
    def __init__(self, origem: BinaryIO) -> None:
        super().__init__()
        if not hasattr(origem, "read"):
            raise TypeError("A origem precisa ser um stream binario (ter .read).")
        self._origem = origem
        self._bytes_lidos = 0

    def readable(self) -> bool:
        return True

    def readinto(self, buffer) -> int:
        if self.closed:
            raise ValueError("Stream fechado.")
        dados = self._origem.read(len(buffer))
        if not dados:
            return 0
        buffer[: len(dados)] = dados
        self._bytes_lidos += len(dados)
        return len(dados)

    def close(self) -> None:
        super().close()

    def _ler_exatamente(self, quantidade: int) -> bytes:
        buffer = bytearray()
        while len(buffer) < quantidade:
            pedaco = self._origem.read(quantidade - len(buffer))
            if not pedaco:
                raise FormatoInvalido(
                    f"Stream terminou cedo: esperava {quantidade} bytes, "
                    f"recebi {len(buffer)}."
                )
            buffer.extend(pedaco)
        self._bytes_lidos += quantidade
        return bytes(buffer)

    def _ler_um_objeto(self) -> POJOSerializavel:
        (tamanho_tipo,) = _TAM_TIPO.unpack(self._ler_exatamente(_TAM_TIPO.size))
        nome_tipo = self._ler_exatamente(tamanho_tipo).decode("utf-8")

        (tamanho_dados,) = _TAM_DADOS.unpack(self._ler_exatamente(_TAM_DADOS.size))
        dados_json = self._ler_exatamente(tamanho_dados).decode("utf-8")

        dicionario = json.loads(dados_json)
        dicionario["_tipo"] = nome_tipo

        return POJOSerializavel.de_dicionario(dicionario)

    def ler_objetos(self) -> List[POJOSerializavel]:
        cabecalho = self._ler_exatamente(_CABECALHO_LOTE.size)
        assinatura, versao, quantidade = _CABECALHO_LOTE.unpack(cabecalho)

        if assinatura != ASSINATURA:
            raise FormatoInvalido(
                f"Assinatura invalida: esperava {ASSINATURA!r}, veio {assinatura!r}."
            )
        if versao != VERSAO_FORMATO:
            raise FormatoInvalido(
                f"Versao de formato {versao} incompativel (esperada {VERSAO_FORMATO})."
            )

        return [self._ler_um_objeto() for _ in range(quantidade)]

    @property
    def bytes_lidos(self) -> int:
        return self._bytes_lidos
