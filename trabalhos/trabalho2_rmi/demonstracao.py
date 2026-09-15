import time

from comum.rmi import ErroRemotoRMI
from trabalho2_rmi.cliente_base import ClienteRMI
from trabalho2_rmi.servidor import montar

def titulo(texto: str) -> None:
    print(f"\n\033[1;34m=== {texto} ===\033[0m")

def main() -> None:
    servidor = montar(porta=0, duracao=300, registrar_log=False)
    servidor.iniciar_em_thread()
    time.sleep(0.2)
    porta = servidor.porta

    titulo("Objetos remotos publicados")
    print(f"  servidor RMI em http://127.0.0.1:{porta}/")
    print("  auth     -> ServicoAutenticacaoRemoto")
    print("  votacao  -> ServicoVotacaoRemoto")
    print("  painel   -> PainelDeNotas")

    titulo("Login: a sessao chega POR REFERENCIA")
    kleyton = ClienteRMI("kleyton", "123", porta=porta)
    kleyton.entrar()
    print(f"  tipo do objeto recebido: {type(kleyton.sessao).__name__}")
    print(f"  referencia: {kleyton.sessao.referencia}")
    print("  -> nao e' uma copia da sessao; e' um proxy. O objeto ficou no servidor.")

    titulo("PASSAGEM POR VALOR: alterar a copia nao afeta o servidor")
    copias = kleyton.urna.listar_candidatos()
    print(f"  antes no cliente : {copias[0].nome} com {copias[0].votos} voto(s)")
    copias[0].votos = 9999
    print(f"  alterado local   : {copias[0].votos} voto(s)")
    print(f"  no servidor      : {kleyton.urna.listar_candidatos()[0].votos} voto(s)")
    print("  -> Candidato e' POJO, nao ObjetoRemoto: viajou por valor.")

    titulo("PASSAGEM POR REFERENCIA: votar pela sessao muda o servidor")
    voto = kleyton.sessao.votar(13)
    print(f"  voto registrado no candidato {voto.numero_candidato}")
    print(f"  no servidor      : {kleyton.urna.listar_candidatos()[0].votos} voto(s)")
    print(f"  ja votei?        : {kleyton.sessao.ja_votei()}")
    print("  -> a chamada executou NO SERVIDOR, sobre o eleitor preso a' sessao.")

    titulo("Referencia devolvida por outra referencia")
    urna = kleyton.sessao.urna()
    print(f"  sessao.urna() -> {type(urna).__name__} {urna.referencia}")

    titulo("Erro de negocio atravessa a rede")
    try:
        kleyton.sessao.votar(22)
    except ErroRemotoRMI as erro:
        print(f"  recusado corretamente -> {erro.tipo}: {erro.mensagem}")

    titulo("Metodo sem @metodo_remoto e' recusado")
    try:
        kleyton.urna.servico()
    except ErroRemotoRMI as erro:
        print(f"  recusado corretamente -> {erro.mensagem}")

    titulo("Callback: o multicast da questao 4 do T1, agora em RMI")
    mariana = ClienteRMI("mariana", "123", porta=porta)
    mariana.entrar()
    admin = ClienteRMI("admin", "admin", porta=porta)
    admin.entrar()

    print(f"\n  inscritos no painel: {admin.painel.inscritos()}")
    print("  admin publica uma nota; o servidor invoca receber_nota em cada cliente:\n")
    admin.painel.publicar("ALERTA", "Faltam 5 minutos!", admin.nome)
    time.sleep(1.0)

    print(f"\n  kleyton recebeu {len(kleyton._receptor.recebidas)} nota(s)")
    print(f"  mariana recebeu {len(mariana._receptor.recebidas)} nota(s)")

    titulo("Administracao: adicionar candidato avisa todo mundo")
    admin.urna.adicionar_candidato(77, "Novo Candidato", "PARTIDO D")
    time.sleep(0.8)

    titulo("Apuracao (por valor)")
    apuracao = admin.urna.apurar()
    for linha in apuracao["resultado"]:
        print(f"  {linha['numero']:>3} {linha['nome']:<16} "
              f"{linha['votos']:>3} voto(s)  {linha['percentual']:>6}%")
    vencedor = apuracao["vencedor"]
    print(f"  total: {apuracao['total_de_votos']} | "
          f"vencedor: {vencedor['nome'] if vencedor else '—'}")

    for cliente in (kleyton, mariana, admin):
        cliente.sair()
    servidor.parar()
    print()

if __name__ == "__main__":
    main()
