import sys

from comum.core.servicos import candidatos_de_exemplo
from trabalho1_votacao.questao1_output_stream.candidato_output_stream import CandidatoOutputStream

def main() -> None:
    candidatos = candidatos_de_exemplo()

    print("=== Questao 1b — destino: saida padrao (System.out) ===")
    print(f"Objetos no array: {len(candidatos)}; serao enviados os 3 primeiros.\n")

    stream = CandidatoOutputStream(sys.stdout.buffer, candidatos, 3)
    total = stream.enviar()

    sys.stdout.buffer.flush()
    print(f"\n\n--> {total} bytes escritos na saida padrao.")
    print("Os caracteres estranhos acima sao os campos binarios de tamanho;")
    print("os trechos legiveis sao o JSON de cada candidato.")

if __name__ == "__main__":
    main()
