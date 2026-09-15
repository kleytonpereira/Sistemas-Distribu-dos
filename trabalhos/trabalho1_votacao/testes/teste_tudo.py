import io
import threading
import time
import unittest

from comum.core.pojos import Administrador, Candidato, Eleitor, NotaInformativa, Voto
from comum.core.protocolo import desempacotar, empacotar, requisicao
from comum.core.servicos import (
    ErroDeServico,
    ServicoAutenticacao,
    ServicoVotacao,
    candidatos_de_exemplo,
    eleitores_de_exemplo,
)
from trabalho1_votacao.questao1_output_stream.candidato_output_stream import CandidatoOutputStream
from trabalho1_votacao.questao2_input_stream.candidato_input_stream import (
    CandidatoInputStream,
    FormatoInvalido,
)

class TestePOJOs(unittest.TestCase):
    def teste_candidato_ida_e_volta(self):
        original = Candidato(numero=13, nome="Ana", partido="PARTIDO A")
        copia = Candidato(**{k: v for k, v in original.para_dicionario().items()
                             if k != "_tipo"})
        self.assertEqual(original, copia)

    def teste_tipo_viaja_no_dicionario(self):
        self.assertEqual(Voto("0001", 13).para_dicionario()["_tipo"], "Voto")
        self.assertEqual(NotaInformativa("ALERTA", "oi").para_dicionario()["_tipo"],
                         "NotaInformativa")

    def teste_heranca_e_agregacao(self):
        from comum.core.pojos import Pessoa
        self.assertTrue(issubclass(Eleitor, Pessoa))
        self.assertTrue(issubclass(Administrador, Pessoa))
        voto = Voto(titulo_eleitor="0001", numero_candidato=13)
        self.assertEqual(voto.numero_candidato, 13)
        self.assertEqual(voto.titulo_eleitor, "0001")

class TesteProtocolo(unittest.TestCase):
    def teste_ida_e_volta(self):
        original = requisicao("VOTAR", numero_candidato=13)
        bytes_na_rede = empacotar(original)

        self.assertEqual(desempacotar(bytes_na_rede[4:]), original)

    def teste_cabecalho_anuncia_tamanho_correto(self):
        import struct
        bytes_na_rede = empacotar({"a": "b"})
        (tamanho,) = struct.unpack("!I", bytes_na_rede[:4])
        self.assertEqual(tamanho, len(bytes_na_rede) - 4)

class TesteStreams(unittest.TestCase):
    def teste_round_trip_em_memoria(self):
        candidatos = candidatos_de_exemplo()

        destino = io.BytesIO()
        CandidatoOutputStream(destino, candidatos, len(candidatos)).enviar()

        destino.seek(0)
        lidos = CandidatoInputStream(destino).ler_objetos()

        self.assertEqual(lidos, candidatos)

    def teste_envia_apenas_a_quantidade_pedida(self):
        candidatos = candidatos_de_exemplo()
        destino = io.BytesIO()
        CandidatoOutputStream(destino, candidatos, 2).enviar()
        destino.seek(0)
        self.assertEqual(len(CandidatoInputStream(destino).ler_objetos()), 2)

    def teste_aceita_array_de_outro_pojo(self):
        votos = [Voto("0001", 13), Voto("0002", 22)]
        destino = io.BytesIO()
        CandidatoOutputStream(destino, votos, len(votos)).enviar()
        destino.seek(0)
        lidos = CandidatoInputStream(destino).ler_objetos()
        self.assertEqual(lidos, votos)
        self.assertIsInstance(lidos[0], Voto)

    def teste_quantidade_maior_que_o_array(self):
        with self.assertRaises(ValueError):
            CandidatoOutputStream(io.BytesIO(), [Candidato(1, "X")], 5)

    def teste_assinatura_invalida_e_detectada(self):
        origem = io.BytesIO(b"LIXOLIXOLIXOLIXO")
        with self.assertRaises(FormatoInvalido):
            CandidatoInputStream(origem).ler_objetos()

    def teste_stream_truncado_e_detectado(self):
        destino = io.BytesIO()
        CandidatoOutputStream(destino, candidatos_de_exemplo(), 4).enviar()
        cortado = io.BytesIO(destino.getvalue()[:20])
        with self.assertRaises(FormatoInvalido):
            CandidatoInputStream(cortado).ler_objetos()

class TesteServicoVotacao(unittest.TestCase):
    def setUp(self):
        self.servico = ServicoVotacao(duracao_segundos=60)
        for candidato in candidatos_de_exemplo():
            self.servico.adicionar_candidato(candidato)
        self.eleitor = eleitores_de_exemplo()[0]

    def teste_voto_valido(self):
        voto = self.servico.registrar_voto(self.eleitor, 13)
        self.assertEqual(voto.numero_candidato, 13)
        self.assertTrue(self.eleitor.ja_votou)

    def teste_voto_duplicado_e_recusado(self):
        self.servico.registrar_voto(self.eleitor, 13)
        with self.assertRaises(ErroDeServico):
            self.servico.registrar_voto(self.eleitor, 22)

    def teste_candidato_inexistente(self):
        with self.assertRaises(ErroDeServico):
            self.servico.registrar_voto(self.eleitor, 1234)

    def teste_candidato_duplicado(self):
        with self.assertRaises(ErroDeServico):
            self.servico.adicionar_candidato(Candidato(13, "Repetido"))

    def teste_prazo_encerrado_recusa_voto(self):
        self.servico.reiniciar_prazo(0)
        self.assertTrue(self.servico.votacao_encerrada())
        with self.assertRaises(ErroDeServico):
            self.servico.registrar_voto(self.eleitor, 13)

    def teste_apuracao_percentuais_e_vencedor(self):
        eleitores = eleitores_de_exemplo()
        self.servico.registrar_voto(eleitores[0], 13)
        self.servico.registrar_voto(eleitores[1], 13)
        self.servico.registrar_voto(eleitores[2], 22)

        apuracao = self.servico.apurar()
        self.assertEqual(apuracao["total_de_votos"], 3)
        self.assertEqual(apuracao["vencedor"]["numero"], 13)

        por_numero = {l["numero"]: l for l in apuracao["resultado"]}
        self.assertAlmostEqual(por_numero[13]["percentual"], 66.67, places=1)
        self.assertAlmostEqual(por_numero[22]["percentual"], 33.33, places=1)

    def teste_apuracao_sem_votos_nao_tem_vencedor(self):
        self.assertIsNone(self.servico.apurar()["vencedor"])

    def teste_votos_concorrentes_nao_se_perdem(self):
        servico = ServicoVotacao(duracao_segundos=60)
        servico.adicionar_candidato(Candidato(13, "Ana"))
        eleitores = [Eleitor(nome=f"E{i}", login=f"e{i}", senha="1", titulo=str(i))
                     for i in range(30)]

        def votar(eleitor):
            servico.registrar_voto(eleitor, 13)

        threads = [threading.Thread(target=votar, args=(e,)) for e in eleitores]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(servico.apurar()["total_de_votos"], 30)

class TesteAutenticacao(unittest.TestCase):
    def setUp(self):
        self.servico = ServicoAutenticacao()
        for eleitor in eleitores_de_exemplo():
            self.servico.cadastrar_eleitor(eleitor)

    def teste_login_valido(self):
        self.assertEqual(self.servico.autenticar("kleyton", "123").nome, "Kleyton")

    def teste_senha_errada(self):
        with self.assertRaises(ErroDeServico):
            self.servico.autenticar("kleyton", "errada")

    def teste_usuario_inexistente(self):
        with self.assertRaises(ErroDeServico):
            self.servico.autenticar("ninguem", "123")

class TesteCamadaSockets(unittest.TestCase):
    def setUp(self):
        from trabalho1_votacao.questao3_serializacao.servidor import criar_servidor
        self.servidor = criar_servidor(porta=0)
        self.servidor.iniciar_em_thread()
        time.sleep(0.1)

    def tearDown(self):
        self.servidor.parar()

    def _cliente(self):
        from comum.sockets import ClienteTCP
        return ClienteTCP("127.0.0.1", self.servidor.porta)

    def teste_fluxo_completo(self):
        with self._cliente() as cliente:
            self.assertEqual(cliente.chamar("LOGIN", login="kleyton",
                                            senha="123")["perfil"], "ELEITOR")
            dados = cliente.chamar("LISTAR_CANDIDATOS")
            self.assertGreaterEqual(len(dados["candidatos"]), 4)

    def teste_operacao_desconhecida_vira_erro(self):
        from comum.sockets import ErroRemoto
        with self._cliente() as cliente:
            with self.assertRaises(ErroRemoto):
                cliente.chamar("OPERACAO_QUE_NAO_EXISTE")

    def teste_erro_de_negocio_vira_erro_remoto(self):
        from comum.sockets import ErroRemoto
        with self._cliente() as cliente:
            with self.assertRaises(ErroRemoto):
                cliente.chamar("LOGIN", login="kleyton", senha="errada")

    def teste_varios_clientes_ao_mesmo_tempo(self):
        with self._cliente() as um, self._cliente() as dois:
            um.chamar("LOGIN", login="mariana", senha="123")
            dois.chamar("LOGIN", login="joao", senha="123")
            self.assertTrue(um.chamar("LISTAR_CANDIDATOS")["candidatos"])
            self.assertTrue(dois.chamar("LISTAR_CANDIDATOS")["candidatos"])

class TesteMulticast(unittest.TestCase):
    GRUPO = "230.0.0.9"
    PORTA = 5099

    def teste_nota_publicada_chega_ao_ouvinte(self):
        from comum.sockets import OuvinteMulticast, PublicadorMulticast

        recebidas = []
        ouvinte = OuvinteMulticast(self.GRUPO, self.PORTA,
                                   lambda nota, remetente: recebidas.append(nota))
        if not ouvinte.entrar():
            self.skipTest("maquina sem suporte a multicast")
        ouvinte.iniciar()

        publicador = PublicadorMulticast(self.GRUPO, self.PORTA)
        try:
            self.assertTrue(publicador.publicar({"tipo": "ALERTA", "mensagem": "oi"}))
            time.sleep(0.5)
            self.assertTrue(any(n["mensagem"] == "oi" for n in recebidas))
        finally:
            publicador.fechar()
            ouvinte.sair()

if __name__ == "__main__":
    unittest.main(verbosity=2)
