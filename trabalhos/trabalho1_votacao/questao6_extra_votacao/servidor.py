import sys
import threading
import time

from comum.core.pojos import Administrador, Candidato, Eleitor, NotaInformativa, TIPOS_DE_NOTA
from comum.core.servicos import (
    ErroDeServico,
    ServicoAutenticacao,
    ServicoVotacao,
    administradores_de_exemplo,
    candidatos_de_exemplo,
    eleitores_de_exemplo,
)
from trabalho1_votacao.questao6_extra_votacao.configuracao import (
    DURACAO_VOTACAO,
    GRUPO_MULTICAST,
    PORTA_MULTICAST,
    PORTA_TCP,
)
from comum.sockets import PublicadorMulticast, ServidorRequisicaoResposta

servico_auth = ServicoAutenticacao()
servico_votacao: ServicoVotacao
publicador = PublicadorMulticast(GRUPO_MULTICAST, PORTA_MULTICAST)

def publicar_nota(tipo: str, mensagem: str, autor: str = "SISTEMA") -> None:
    nota = NotaInformativa(tipo=tipo, mensagem=f"[{autor}] {mensagem}")
    if publicador.publicar(nota.para_dicionario()):
        print(f"[multicast] {tipo} ({autor}): {mensagem}")

def vigiar_prazo(duracao: int) -> None:
    marcos = [m for m in (60, 30, 10) if m < duracao]
    marcos_ja_avisados = set()

    while True:
        restante = servico_votacao.segundos_restantes()

        if restante <= 0:
            publicar_nota("ALERTA", "VOTACAO ENCERRADA. Apurando resultados...")
            time.sleep(0.3)

            apuracao = servico_votacao.apurar()
            vencedor = apuracao["vencedor"]
            resumo = " | ".join(f"{l['nome']}: {l['votos']} ({l['percentual']}%)"
                                for l in apuracao["resultado"])
            publicar_nota("ATUALIZACAO",
                          f"Total de votos: {apuracao['total_de_votos']}. {resumo}")
            publicar_nota("ATUALIZACAO",
                          f"VENCEDOR: {vencedor['nome']} com {vencedor['votos']} "
                          f"voto(s) ({vencedor['percentual']}%)" if vencedor
                          else "Nenhum voto registrado.")

            print("\n[servidor] === APURACAO FINAL ===")
            for linha in apuracao["resultado"]:
                print(f"  {linha['numero']:>3} {linha['nome']:<16} "
                      f"{linha['votos']:>3} voto(s)  {linha['percentual']:>6}%")
            print(f"  total: {apuracao['total_de_votos']} | "
                  f"vencedor: {vencedor['nome'] if vencedor else '—'}\n")
            return

        for marco in marcos:
            if restante <= marco and marco not in marcos_ja_avisados:
                marcos_ja_avisados.add(marco)
                publicar_nota("ALERTA", f"Faltam {marco} segundos para o encerramento!")

        time.sleep(1)

def _exigir_login(sessao):
    pessoa = sessao.get("pessoa")
    if pessoa is None:
        raise ErroDeServico("Faca login primeiro.")
    return pessoa

def _exigir_admin(sessao):
    pessoa = _exigir_login(sessao)
    if not isinstance(pessoa, Administrador):
        raise ErroDeServico("Operacao permitida apenas para administradores.")
    return pessoa

def login(dados, sessao):
    pessoa = servico_auth.autenticar(dados["login"], dados["senha"])
    sessao["pessoa"] = pessoa
    return {
        "nome": pessoa.nome,
        "perfil": "ADMIN" if isinstance(pessoa, Administrador) else "ELEITOR",
        "candidatos": [c.para_dicionario() for c in servico_votacao.listar_candidatos()],
        "segundos_restantes": servico_votacao.segundos_restantes(),
        "grupo_multicast": GRUPO_MULTICAST,
        "porta_multicast": PORTA_MULTICAST,
    }

def listar_candidatos(dados, sessao):
    _exigir_login(sessao)
    return {
        "candidatos": [c.para_dicionario() for c in servico_votacao.listar_candidatos()],
        "segundos_restantes": servico_votacao.segundos_restantes(),
    }

def votar(dados, sessao):
    pessoa = _exigir_login(sessao)
    if not isinstance(pessoa, Eleitor):
        raise ErroDeServico("Administradores nao votam.")
    voto = servico_votacao.registrar_voto(pessoa, int(dados["numero_candidato"]))
    return {"voto": voto.para_dicionario()}

def adicionar_candidato(dados, sessao):
    admin = _exigir_admin(sessao)
    candidato = Candidato(numero=int(dados["numero"]),
                          nome=dados["nome"],
                          partido=dados.get("partido", "SEM PARTIDO"))
    servico_votacao.adicionar_candidato(candidato)

    publicar_nota("ATUALIZACAO",
                  f"Novo candidato: {candidato.numero} - {candidato.nome}",
                  autor=admin.nome)
    return {"candidato": candidato.para_dicionario()}

def remover_candidato(dados, sessao):
    admin = _exigir_admin(sessao)
    candidato = servico_votacao.remover_candidato(int(dados["numero"]))
    publicar_nota("ATUALIZACAO",
                  f"Candidato removido: {candidato.numero} - {candidato.nome}",
                  autor=admin.nome)
    return {"removido": candidato.para_dicionario()}

def enviar_nota(dados, sessao):
    admin = _exigir_admin(sessao)
    tipo = dados.get("tipo", "NOTIFICACAO")
    if tipo not in TIPOS_DE_NOTA:
        raise ErroDeServico(f"Tipo invalido. Use um de {TIPOS_DE_NOTA}.")
    publicar_nota(tipo, dados["mensagem"], autor=admin.nome)
    return {"publicada": True}

def apurar(dados, sessao):
    _exigir_login(sessao)
    return servico_votacao.apurar()

OPERACOES = {
    "LOGIN": login,
    "LISTAR_CANDIDATOS": listar_candidatos,
    "VOTAR": votar,
    "ADICIONAR_CANDIDATO": adicionar_candidato,
    "REMOVER_CANDIDATO": remover_candidato,
    "ENVIAR_NOTA": enviar_nota,
    "APURAR": apurar,
}

def main() -> None:
    global servico_votacao

    duracao = int(sys.argv[1]) if len(sys.argv) > 1 else DURACAO_VOTACAO
    servico_votacao = ServicoVotacao(duracao_segundos=duracao)

    for candidato in candidatos_de_exemplo():
        servico_votacao.adicionar_candidato(candidato)
    for eleitor in eleitores_de_exemplo():
        servico_auth.cadastrar_eleitor(eleitor)
    for admin in administradores_de_exemplo():
        servico_auth.cadastrar_administrador(admin)

    threading.Thread(target=vigiar_prazo, args=(duracao,), daemon=True).start()

    print(f"[servidor] TCP (login/lista/voto) na porta {PORTA_TCP}")
    print(f"[servidor] Multicast (notas) em {GRUPO_MULTICAST}:{PORTA_MULTICAST}")
    print(f"[servidor] Prazo da votacao: {duracao}s")
    print("[servidor] Eleitores: kleyton/mariana/joao (senha 123) | admin/admin\n")

    ServidorRequisicaoResposta(
        PORTA_TCP, OPERACOES, nome="votacao",
        erros_de_negocio=(ErroDeServico,), registrar=False,
    ).iniciar(anunciar=False)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[servidor] Encerrado pelo usuario.")
