import sys

from comum.core.servicos import candidatos_de_exemplo
from trabalho1_votacao.questao1_output_stream.candidato_output_stream import CandidatoOutputStream

def main() -> None:
    candidatos = candidatos_de_exemplo()
    CandidatoOutputStream(sys.stdout.buffer, candidatos, len(candidatos)).enviar()
    sys.stdout.buffer.flush()

if __name__ == "__main__":
    main()
