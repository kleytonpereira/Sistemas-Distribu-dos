import socket

from comum.core.pojos import Voto
from trabalho1_votacao.questao1_output_stream.candidato_output_stream import CandidatoOutputStream

HOST = "127.0.0.1"
PORTA = 5002

def main() -> None:
    votos = [
        Voto(titulo_eleitor="0001", numero_candidato=13),
        Voto(titulo_eleitor="0002", numero_candidato=22),
        Voto(titulo_eleitor="0003", numero_candidato=13),
    ]

    print("=== Questao 2d — origem: cliente remoto (TCP) ===")
    print(f"Enviando {len(votos)} votos para {HOST}:{PORTA} ...")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as conexao:
        conexao.connect((HOST, PORTA))
        with conexao.makefile("wb") as saida_do_socket:
            CandidatoOutputStream(saida_do_socket, votos, len(votos)).enviar()
        conexao.shutdown(socket.SHUT_WR)

    print("Enviado. Confira a saida do servidor_decodificador_tcp.")

if __name__ == "__main__":
    main()
