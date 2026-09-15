import sys

from trabalho1_votacao.questao2_input_stream.candidato_input_stream import CandidatoInputStream

def main() -> None:
    stream = CandidatoInputStream(sys.stdin.buffer)
    objetos = stream.ler_objetos()

    print("=== Questao 2b — origem: entrada padrao (System.in) ===")
    print(f"{len(objetos)} objetos reconstruidos / {stream.bytes_lidos} bytes lidos:\n")
    for objeto in objetos:
        print("  ", objeto)

if __name__ == "__main__":
    main()
