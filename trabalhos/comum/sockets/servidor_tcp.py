from __future__ import annotations

import socket
import threading
from typing import Callable, Dict, Optional, Tuple, Type

from comum.core.protocolo import resposta_erro, resposta_ok
from comum.sockets.enquadramento import enviar_mensagem, receber_mensagem

Manipulador = Callable[[socket.socket, Tuple[str, int]], None]

Operacao = Callable[[dict, dict], Optional[dict]]

class ServidorTCP:
    def __init__(self,
                 porta: int,
                 manipulador: Manipulador,
                 host: str = "0.0.0.0",
                 fila: int = 10,
                 nome: str = "servidor") -> None:
        self.host = host
        self.porta = porta
        self.nome = nome
        self._manipulador = manipulador
        self._fila = fila
        self._socket: Optional[socket.socket] = None
        self._rodando = False

    def abrir(self) -> None:
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self._socket.bind((self.host, self.porta))
        self._socket.listen(self._fila)

        self.porta = self._socket.getsockname()[1]
        self._rodando = True

    def iniciar(self, anunciar: bool = True) -> None:
        if self._socket is None:
            self.abrir()
        if anunciar:
            print(f"[{self.nome}] escutando em {self.host}:{self.porta}")

        while self._rodando:
            try:
                conexao, endereco = self._socket.accept()
            except OSError:
                break

            threading.Thread(
                target=self._envolver,
                args=(conexao, endereco),
                daemon=True,
            ).start()

    def _envolver(self, conexao: socket.socket, endereco) -> None:
        with conexao:
            try:
                self._manipulador(conexao, endereco)
            except (ConnectionError, OSError) as erro:
                print(f"[{self.nome}] {endereco[0]}:{endereco[1]} caiu: {erro}")
            except Exception as erro:
                print(f"[{self.nome}] falha inesperada: {erro!r}")

    def iniciar_em_thread(self) -> threading.Thread:
        if self._socket is None:
            self.abrir()
        thread = threading.Thread(target=self.iniciar, kwargs={"anunciar": False},
                                  daemon=True)
        thread.start()
        return thread

    def parar(self) -> None:
        self._rodando = False
        if self._socket is not None:
            self._socket.close()
            self._socket = None

class ServidorRequisicaoResposta(ServidorTCP):
    def __init__(self,
                 porta: int,
                 operacoes: Dict[str, Operacao],
                 host: str = "0.0.0.0",
                 nome: str = "servidor",
                 erros_de_negocio: Tuple[Type[Exception], ...] = (),
                 ao_conectar: Optional[Callable[[dict], None]] = None,
                 registrar: bool = True) -> None:
        super().__init__(porta, self._atender, host=host, nome=nome)
        self._operacoes = operacoes
        self._erros_de_negocio = tuple(erros_de_negocio)
        self._ao_conectar = ao_conectar
        self._registrar = registrar

    def _atender(self, conexao: socket.socket, endereco) -> None:
        etiqueta = f"{endereco[0]}:{endereco[1]}"
        sessao: dict = {}
        if self._ao_conectar:
            self._ao_conectar(sessao)
        if self._registrar:
            print(f"[{self.nome}] {etiqueta} conectado")

        while True:
            requisicao = receber_mensagem(conexao)
            if requisicao is None:
                break
            if self._registrar:
                print(f"[{self.nome}] {etiqueta} -> {requisicao.get('operacao')}")
            enviar_mensagem(conexao, self.despachar(requisicao, sessao))

        if self._registrar:
            print(f"[{self.nome}] {etiqueta} desconectado")

    def despachar(self, requisicao: dict, sessao: dict) -> dict:
        nome_operacao = requisicao.get("operacao")
        dados = requisicao.get("dados", {})

        operacao = self._operacoes.get(nome_operacao)
        if operacao is None:
            return resposta_erro(f"Operacao desconhecida: {nome_operacao!r}")

        try:
            return resposta_ok(**(operacao(dados, sessao) or {}))
        except self._erros_de_negocio as erro:

            return resposta_erro(str(erro))
        except (KeyError, ValueError) as erro:

            return resposta_erro(f"Requisicao invalida: {erro}")
