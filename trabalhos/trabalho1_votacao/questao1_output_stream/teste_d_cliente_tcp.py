import socket

from comum.core.servicos import candidatos_de_exemplo
from trabalho1_votacao.questao1_output_stream.candidato_output_stream import CandidatoOutputStream

HOST = "127.0.0.1"
PORTA = 5001

def main() -> None:
    candidatos = candidatos_de_exemplo()

    print("=== Questao 1d — destino: servidor remoto (TCP) ===")
    print(f"Conectando em {HOST}:{PORTA} ...")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as conexao:
        conexao.connect((HOST, PORTA))

        with conexao.makefile("wb") as saida_do_socket:
            stream = CandidatoOutputStream(saida_do_socket, candidatos, len(candidatos))
            total = stream.enviar()

        conexao.shutdown(socket.SHUT_WR)

    print(f"{len(candidatos)} candidatos enviados / {total} bytes.")
    print("Confira a saida do servidor_coletor_tcp.")

if __name__ == "__main__":
    main()
