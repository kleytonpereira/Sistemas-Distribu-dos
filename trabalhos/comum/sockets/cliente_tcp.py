from __future__ import annotations

import socket
from typing import Any, Dict, Optional

from comum.core.protocolo import requisicao
from comum.sockets.enquadramento import enviar_mensagem, receber_mensagem

class ErroRemoto(Exception):
    pass

class ClienteTCP:
    def __init__(self, host: str = "127.0.0.1", porta: int = 5000) -> None:
        self.host = host
        self.porta = porta
        self._conexao: Optional[socket.socket] = None

    def conectar(self) -> "ClienteTCP":
        self._conexao = socket.create_connection((self.host, self.porta))
        return self

    def fechar(self) -> None:
        if self._conexao is not None:
            self._conexao.close()
            self._conexao = None

    def __enter__(self) -> "ClienteTCP":
        return self.conectar() if self._conexao is None else self

    def __exit__(self, *_) -> None:
        self.fechar()

    def chamar(self, operacao: str, **dados: Any) -> Dict[str, Any]:
        if self._conexao is None:
            self.conectar()

        enviar_mensagem(self._conexao, requisicao(operacao, **dados))
        resposta = receber_mensagem(self._conexao)

        if resposta is None:
            raise ErroRemoto("O servidor fechou a conexao.")
        if resposta.get("status") != "OK":
            raise ErroRemoto(resposta["dados"].get("mensagem", "erro desconhecido"))
        return resposta["dados"]

    def tentar(self, operacao: str, **dados: Any) -> Optional[Dict[str, Any]]:
        try:
            return self.chamar(operacao, **dados)
        except ErroRemoto as erro:
            print(f"  ERRO: {erro}")
            return None
