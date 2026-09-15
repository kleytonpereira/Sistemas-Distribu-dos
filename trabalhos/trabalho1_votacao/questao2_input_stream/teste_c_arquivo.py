from pathlib import Path

from comum.core.servicos import candidatos_de_exemplo
from trabalho1_votacao.questao2_input_stream.candidato_input_stream import CandidatoInputStream

ARQUIVO_ENTRADA = Path(__file__).resolve().parents[1] / "dados" / "candidatos.pojo"

def main() -> None:
    if not ARQUIVO_ENTRADA.exists():
        print(f"Arquivo {ARQUIVO_ENTRADA} nao existe.")
        print("Rode antes: python3 -m trabalho1_votacao.questao1_output_stream.teste_c_arquivo")
        return

    print("=== Questao 2c — origem: arquivo (FileInputStream) ===")

    with open(ARQUIVO_ENTRADA, "rb") as arquivo:
        stream = CandidatoInputStream(arquivo)
        objetos = stream.ler_objetos()

    print(f"{len(objetos)} objetos reconstruidos / {stream.bytes_lidos} bytes lidos:\n")
    for objeto in objetos:
        print("  ", objeto)

    originais = candidatos_de_exemplo()
    print("\nRound-trip (objetos lidos == objetos originais)?",
          "SIM" if objetos == originais else "NAO")

if __name__ == "__main__":
    main()
