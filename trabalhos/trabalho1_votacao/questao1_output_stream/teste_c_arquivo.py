from pathlib import Path

from comum.core.servicos import candidatos_de_exemplo
from trabalho1_votacao.questao1_output_stream.candidato_output_stream import CandidatoOutputStream

ARQUIVO_SAIDA = Path(__file__).resolve().parents[1] / "dados" / "candidatos.pojo"

def main() -> None:
    candidatos = candidatos_de_exemplo()
    ARQUIVO_SAIDA.parent.mkdir(parents=True, exist_ok=True)

    print("=== Questao 1c — destino: arquivo (FileOutputStream) ===")

    with open(ARQUIVO_SAIDA, "wb") as arquivo:
        stream = CandidatoOutputStream(arquivo, candidatos, len(candidatos))
        total = stream.enviar()

    print(f"Arquivo gerado: {ARQUIVO_SAIDA}")
    print(f"{len(candidatos)} objetos / {total} bytes.")

    primeiros = ARQUIVO_SAIDA.read_bytes()[:16]
    print("Primeiros 16 bytes:", primeiros.hex(" "))
    print("Leia esse arquivo de volta com a Questao 2 (teste_c_arquivo).")

if __name__ == "__main__":
    main()
