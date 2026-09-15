import sys

from comum.core.servicos import (
    ServicoAutenticacao,
    ServicoVotacao,
    administradores_de_exemplo,
    candidatos_de_exemplo,
    eleitores_de_exemplo,
)
from comum.rmi import ServidorRMI
from trabalho2_rmi.configuracao import DURACAO_VOTACAO, HOST_SERVIDOR, PORTA_SERVIDOR
from trabalho2_rmi.objetos_remotos import (
    PainelDeNotas,
    ServicoAutenticacaoRemoto,
    ServicoVotacaoRemoto,
)

def montar(porta: int = PORTA_SERVIDOR, duracao: int = DURACAO_VOTACAO,
           registrar_log: bool = True) -> ServidorRMI:

    servico_votacao = ServicoVotacao(duracao_segundos=duracao)
    servico_auth = ServicoAutenticacao()

    for candidato in candidatos_de_exemplo():
        servico_votacao.adicionar_candidato(candidato)
    for eleitor in eleitores_de_exemplo():
        servico_auth.cadastrar_eleitor(eleitor)
    for admin in administradores_de_exemplo():
        servico_auth.cadastrar_administrador(admin)

    painel = PainelDeNotas()
    votacao_remota = ServicoVotacaoRemoto(servico_votacao, painel)
    auth_remoto = ServicoAutenticacaoRemoto(servico_auth, votacao_remota)

    servidor = ServidorRMI(porta=porta, host=HOST_SERVIDOR,
                           registrar_log=registrar_log)

    servidor.registrar("auth", auth_remoto)
    servidor.registrar("votacao", votacao_remota)
    servidor.registrar("painel", painel)

    return servidor

def main() -> None:
    duracao = int(sys.argv[1]) if len(sys.argv) > 1 else DURACAO_VOTACAO
    servidor = montar(duracao=duracao)

    print(f"[servidor] prazo da votacao: {duracao}s")
    print("[servidor] eleitores: kleyton/mariana/joao (senha 123) | admin/admin")
    print("[servidor] objetos publicados: auth, votacao, painel\n")

    servidor.iniciar()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[servidor] Encerrado pelo usuario.")
