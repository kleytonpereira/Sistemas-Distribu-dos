import socket

from trabalho1_votacao.questao2_input_stream.candidato_input_stream import (
    CandidatoInputStream,
    FormatoInvalido,
)
from comum.sockets import ServidorTCP

PORTA = 5002

def decodificar(conexao: socket.socket, endereco) -> None:
    etiqueta = f"{endereco[0]}:{endereco[1]}"
    try:

        with conexao.makefile("rb") as entrada_do_socket:
            stream = CandidatoInputStream(entrada_do_socket)
            objetos = stream.ler_objetos()

        print(f"[{etiqueta}] {len(objetos)} objetos recebidos "
              f"({stream.bytes_lidos} bytes):")
        for objeto in objetos:
            print(f"[{etiqueta}]    {objeto}")
    except FormatoInvalido as erro:

        print(f"[{etiqueta}] dados invalidos: {erro}")
    finally:
        print(f"[{etiqueta}] conexao encerrada.\n")

def main() -> None:
    ServidorTCP(PORTA, decodificar, nome="decodificador").iniciar()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[decodificador] Encerrado pelo usuario.")
