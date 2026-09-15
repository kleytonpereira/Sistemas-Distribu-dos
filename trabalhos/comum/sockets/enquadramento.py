from __future__ import annotations

import socket
from typing import Any, Dict, Optional

from comum.core.protocolo import TAMANHO_CABECALHO, cabecalho, desempacotar, empacotar

def _receber_exatamente(conexao: socket.socket, quantidade: int) -> Optional[bytes]:
    buffer = bytearray()
    while len(buffer) < quantidade:
        pedaco = conexao.recv(quantidade - len(buffer))
        if not pedaco:
            return None
        buffer.extend(pedaco)
    return bytes(buffer)

def enviar_mensagem(conexao: socket.socket, objeto: Dict[str, Any]) -> None:
    conexao.sendall(empacotar(objeto))

def receber_mensagem(conexao: socket.socket) -> Optional[Dict[str, Any]]:
    bytes_cabecalho = _receber_exatamente(conexao, TAMANHO_CABECALHO)
    if bytes_cabecalho is None:
        return None
    (tamanho,) = cabecalho.unpack(bytes_cabecalho)
    corpo = _receber_exatamente(conexao, tamanho)
    if corpo is None:
        return None
    return desempacotar(corpo)
