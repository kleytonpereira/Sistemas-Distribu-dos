from comum.core.pojos import Candidato, Eleitor
from comum.core.servicos import (
    ErroDeServico,
    ServicoAutenticacao,
    ServicoVotacao,
    administradores_de_exemplo,
    candidatos_de_exemplo,
    eleitores_de_exemplo,
)
from comum.sockets import ServidorRequisicaoResposta

PORTA = 5003

servico_auth = ServicoAutenticacao()
servico_votacao = ServicoVotacao(duracao_segundos=600)

def preparar_dados_iniciais() -> None:
    if servico_votacao.listar_candidatos():
        return
    for candidato in candidatos_de_exemplo():
        servico_votacao.adicionar_candidato(candidato)
    for eleitor in eleitores_de_exemplo():
        servico_auth.cadastrar_eleitor(eleitor)
    for admin in administradores_de_exemplo():
        servico_auth.cadastrar_administrador(admin)

def listar_candidatos(dados, sessao):
    candidatos = servico_votacao.listar_candidatos()

    return {
        "candidatos": [c.para_dicionario() for c in candidatos],
        "segundos_restantes": servico_votacao.segundos_restantes(),
    }

def login(dados, sessao):
    pessoa = servico_auth.autenticar(dados["login"], dados["senha"])
    sessao["pessoa"] = pessoa
    return {
        "pessoa": pessoa.para_dicionario(),
        "perfil": "ELEITOR" if isinstance(pessoa, Eleitor) else "ADMIN",
    }

def votar(dados, sessao):
    eleitor = servico_auth.buscar_eleitor(dados["login"])
    if eleitor is None:
        raise ErroDeServico("Eleitor nao encontrado. Faca login antes.")
    voto = servico_votacao.registrar_voto(eleitor, int(dados["numero_candidato"]))
    return {"voto": voto.para_dicionario()}

def adicionar_candidato(dados, sessao):
    candidato = Candidato(numero=int(dados["numero"]),
                          nome=dados["nome"],
                          partido=dados.get("partido", "SEM PARTIDO"))
    servico_votacao.adicionar_candidato(candidato)
    return {"candidato": candidato.para_dicionario()}

def apurar(dados, sessao):
    return servico_votacao.apurar()

OPERACOES = {
    "LISTAR_CANDIDATOS": listar_candidatos,
    "LOGIN": login,
    "VOTAR": votar,
    "ADICIONAR_CANDIDATO": adicionar_candidato,
    "APURAR": apurar,
}

def criar_servidor(porta: int = PORTA) -> ServidorRequisicaoResposta:
    preparar_dados_iniciais()
    return ServidorRequisicaoResposta(
        porta,
        OPERACOES,
        nome="questao3",

        erros_de_negocio=(ErroDeServico,),
    )

def main() -> None:
    criar_servidor().iniciar()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[questao3] Encerrado pelo usuario.")
