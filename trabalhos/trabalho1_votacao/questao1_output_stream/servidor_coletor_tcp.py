import socket
from pathlib import Path

from comum.sockets import ServidorTCP

PORTA = 5001
ARQUIVO_RECEBIDO = Path(__file__).resolve().parents[1] / "dados" / "recebido_tcp.pojo"

def coletar(conexao: socket.socket, endereco) -> None:
    etiqueta = f"{endereco[0]}:{endereco[1]}"
    print(f"[coletor] conexao de {etiqueta}")

    recebidos = bytearray()
    while True:

        pedaco = conexao.recv(4096)
        if not pedaco:

            break
        recebidos.extend(pedaco)

    ARQUIVO_RECEBIDO.parent.mkdir(parents=True, exist_ok=True)
    ARQUIVO_RECEBIDO.write_bytes(bytes(recebidos))

    print(f"[coletor] {len(recebidos)} bytes recebidos")

    print(f"[coletor] primeiros 16 bytes: {bytes(recebidos[:16]).hex(' ')}")
    print(f"[coletor] salvo em {ARQUIVO_RECEBIDO}")
    print("[coletor] (para decodificar, use a Questao 2)\n")

def main() -> None:
    ServidorTCP(PORTA, coletar, nome="coletor").iniciar()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[coletor] Encerrado pelo usuario.")
