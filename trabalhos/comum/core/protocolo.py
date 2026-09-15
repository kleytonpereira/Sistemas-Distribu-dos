from __future__ import annotations

import json
import struct
from typing import Any, Dict

cabecalho = struct.Struct("!I")
TAMANHO_CABECALHO = cabecalho.size
TAMANHO_MAXIMO_MENSAGEM = 8 * 1024 * 1024

def empacotar(objeto: Dict[str, Any]) -> bytes:
    corpo = json.dumps(objeto, ensure_ascii=False).encode("utf-8")
    if len(corpo) > TAMANHO_MAXIMO_MENSAGEM:
        raise ValueError(f"Mensagem grande demais: {len(corpo)} bytes")
    return cabecalho.pack(len(corpo)) + corpo

def desempacotar(corpo: bytes) -> Dict[str, Any]:
    return json.loads(corpo.decode("utf-8"))

def requisicao(operacao: str, **dados: Any) -> Dict[str, Any]:
    return {"operacao": operacao, "dados": dados}

def resposta_ok(**dados: Any) -> Dict[str, Any]:
    return {"status": "OK", "dados": dados}

def resposta_erro(mensagem: str) -> Dict[str, Any]:
    return {"status": "ERRO", "dados": {"mensagem": mensagem}}
