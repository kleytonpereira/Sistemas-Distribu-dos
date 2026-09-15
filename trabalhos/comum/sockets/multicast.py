from __future__ import annotations

import os
import socket
import struct
import threading
import time
from typing import Any, Callable, Dict, Optional

from comum.core.protocolo import desempacotar, empacotar
from comum.core.protocolo import TAMANHO_CABECALHO

TAMANHO_BUFFER_UDP = 4096
TTL_PADRAO = 1

def endereco_da_interface() -> str:
    configurado = os.environ.get("SD_INTERFACE")
    if configurado:
        return configurado
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sonda:
            sonda.connect(("8.8.8.8", 80))
            return sonda.getsockname()[0]
    except OSError:
        return "0.0.0.0"

DICA_DE_REDE = (
    "\n  DICA: multicast exige uma interface de rede com suporte a multicast.\n"
    "  - Em maquina sem rede (container, VM isolada) isso falha mesmo.\n"
    "  - Para forcar uma interface especifica:\n"
    "        SD_INTERFACE=<seu_ip_local> python3 -m <modulo>\n"
    "    (descubra seu IP com:  ip -4 addr show | grep inet)\n"
)

def _membresia(grupo: str) -> bytes:
    return struct.pack("4s4s",
                       socket.inet_aton(grupo),
                       socket.inet_aton(endereco_da_interface()))

class PublicadorMulticast:
    def __init__(self, grupo: str, porta: int, ttl: int = TTL_PADRAO) -> None:
        self.grupo = grupo
        self.porta = porta
        self._trava = threading.Lock()
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self._socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL,
                                struct.pack("b", ttl))

        self._socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)

        interface = endereco_da_interface()
        if interface != "0.0.0.0":
            try:
                self._socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF,
                                        socket.inet_aton(interface))
            except OSError as erro:
                print(f"[multicast] interface {interface} recusada: {erro}")

    def publicar(self, objeto: Dict[str, Any]) -> bool:
        dados = empacotar(objeto)[TAMANHO_CABECALHO:]
        try:
            with self._trava:
                self._socket.sendto(dados, (self.grupo, self.porta))
        except OSError as erro:
            print(f"[multicast] FALHA ao enviar: {erro}")
            print(DICA_DE_REDE)
            return False
        return True

    def fechar(self) -> None:
        self._socket.close()

class OuvinteMulticast:
    def __init__(self, grupo: str, porta: int,
                 ao_receber: Callable[[Dict[str, Any], str], None]) -> None:
        self.grupo = grupo
        self.porta = porta
        self._ao_receber = ao_receber
        self._socket: Optional[socket.socket] = None

        self._parar = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def entrar(self) -> bool:
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind(("", self.porta))
        try:
            self._socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
                                    _membresia(self.grupo))
        except OSError as erro:
            print(f"Nao consegui entrar no grupo multicast: {erro}")
            print(DICA_DE_REDE)
            self._socket.close()
            self._socket = None
            return False

        self._socket.settimeout(1.0)
        return True

    def iniciar(self) -> None:
        self._thread = threading.Thread(target=self._escutar, daemon=True)
        self._thread.start()

    def _escutar(self) -> None:
        while not self._parar.is_set():
            try:
                dados, remetente = self._socket.recvfrom(TAMANHO_BUFFER_UDP)
            except socket.timeout:
                continue
            except OSError:
                break
            try:
                objeto = desempacotar(dados)
            except ValueError:
                continue
            self._ao_receber(objeto, remetente[0])

    def sair(self) -> None:
        self._parar.set()
        if self._thread is not None:
            self._thread.join(timeout=2)
        if self._socket is not None:
            try:
                self._socket.setsockopt(socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP,
                                        _membresia(self.grupo))
            except OSError:
                pass
            self._socket.close()
            self._socket = None

def formatar_nota(nota: Dict[str, Any], remetente: str = "") -> str:
    instante = time.strftime("%H:%M:%S", time.localtime(nota.get("timestamp", 0)))
    origem = f"   (de {remetente})" if remetente else ""
    return f"[{instante}] <{nota.get('tipo')}> {nota.get('mensagem')}{origem}"
