import threading
import time
import unittest

from comum.core.pojos import Candidato, NotaInformativa
from comum.rmi import (
    ErroRemotoRMI,
    Mensagem,
    ObjetoRemoto,
    RemoteObjectRef,
    TIPO_REQUISICAO,
    TIPO_RESPOSTA,
    desempacotar_valores,
    empacotar_valores,
    metodo_remoto,
)
from comum.rmi.transporte import getRequest, sendReply
from trabalho2_rmi.cliente_base import ClienteRMI, ReceptorDeNotas
from trabalho2_rmi.servidor import montar

class TesteMensagem(unittest.TestCase):
    def teste_ida_e_volta(self):
        original = Mensagem(TIPO_REQUISICAO, 42, "votacao", "apurar", b"{}")
        copia = Mensagem.desempacotar(original.empacotar())
        self.assertEqual(copia, original)

    def teste_campos_do_enunciado(self):
        m = Mensagem.desempacotar(
            Mensagem(TIPO_RESPOSTA, 7, "sessao#3", "votar", b'{"valor": 1}').empacotar())
        self.assertEqual(m.tipo, TIPO_RESPOSTA)
        self.assertEqual(m.id_requisicao, 7)
        self.assertEqual(m.referencia_objeto, "sessao#3")
        self.assertEqual(m.id_metodo, "votar")
        self.assertEqual(m.argumentos, b'{"valor": 1}')

    def teste_get_request_recusa_resposta(self):
        resposta = Mensagem(TIPO_RESPOSTA, 1, "x", "y", b"").empacotar()
        with self.assertRaises(ValueError):
            getRequest(resposta)

    def teste_send_reply_copia_o_id(self):
        bytes_resposta = sendReply(b'{"valor": 9}', 55, "votacao", "apurar")
        m = Mensagem.desempacotar(bytes_resposta)
        self.assertEqual(m.tipo, TIPO_RESPOSTA)
        self.assertEqual(m.id_requisicao, 55)

class TesteRepresentacaoExterna(unittest.TestCase):
    def teste_pojo_ida_e_volta(self):
        original = Candidato(13, "Ana", "PARTIDO A")
        copia = desempacotar_valores(empacotar_valores(original))
        self.assertEqual(copia, original)
        self.assertIsInstance(copia, Candidato)

    def teste_estrutura_aninhada(self):
        dados = {"lista": [Candidato(1, "A"), Candidato(2, "B")], "n": 2}
        volta = desempacotar_valores(empacotar_valores(dados))
        self.assertEqual(volta["n"], 2)
        self.assertEqual(volta["lista"][1].nome, "B")

    def teste_referencia_vira_proxy(self):
        ref = RemoteObjectRef("127.0.0.1", 9000, 1, 1, "Urna", "votacao")
        marcados = []
        volta = desempacotar_valores(empacotar_valores(ref),
                                     criar_proxy=lambda r: marcados.append(r) or "PROXY")
        self.assertEqual(volta, "PROXY")
        self.assertEqual(marcados[0], ref)

class TesteObjetoRemoto(unittest.TestCase):
    class Exemplo(ObjetoRemoto):
        @metodo_remoto
        def publico(self):
            return 1

        def privado(self):
            return 2

    def teste_so_metodos_decorados_sao_remotos(self):
        self.assertEqual(self.Exemplo.metodos_remotos(), {"publico"})
        alvo = self.Exemplo()
        self.assertTrue(alvo.pode_invocar("publico"))
        self.assertFalse(alvo.pode_invocar("privado"))

    def teste_pojo_nao_e_objeto_remoto(self):
        self.assertNotIsInstance(Candidato(1, "A"), ObjetoRemoto)

class TesteIntegracaoRMI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.servidor = montar(porta=0, duracao=120, registrar_log=False)
        cls.servidor.iniciar_em_thread()
        time.sleep(0.2)
        cls.porta = cls.servidor.porta

    @classmethod
    def tearDownClass(cls):
        cls.servidor.parar()

    def _cliente(self, login="kleyton", senha="123"):
        cliente = ClienteRMI(login, senha, porta=self.porta)
        self.assertTrue(cliente.entrar())
        self.addCleanup(cliente.sair)
        return cliente

    def teste_metodos_remotos_respondem(self):
        cliente = self._cliente("joao")
        self.assertTrue(cliente.urna.listar_candidatos())
        self.assertGreater(cliente.urna.segundos_restantes(), 0)
        self.assertIn("resultado", cliente.urna.apurar())
        self.assertFalse(cliente.sessao.ja_votei())

    def teste_alterar_copia_nao_afeta_servidor(self):
        cliente = self._cliente("mariana")
        copias = cliente.urna.listar_candidatos()
        copias[0].votos = 9999
        de_novo = cliente.urna.listar_candidatos()
        self.assertEqual(de_novo[0].votos, 0)

    def teste_sessao_chega_como_proxy(self):
        cliente = self._cliente()

        self.assertEqual(cliente.sessao.quem_sou().login, "kleyton")

    def teste_voto_pela_sessao_muda_o_servidor(self):
        cliente = self._cliente()
        antes = cliente.urna.listar_candidatos()[0].votos
        cliente.sessao.votar(13)
        depois = cliente.urna.listar_candidatos()[0].votos
        self.assertEqual(depois, antes + 1)
        self.assertTrue(cliente.sessao.ja_votei())

    def teste_referencia_devolvida_por_outra_referencia(self):
        cliente = self._cliente("joao")
        urna = cliente.sessao.urna()
        self.assertTrue(urna.listar_candidatos())

    def teste_erro_de_negocio_chega_ao_cliente(self):
        cliente = self._cliente("mariana")
        cliente.sessao.votar(22)
        with self.assertRaises(ErroRemotoRMI):
            cliente.sessao.votar(13)

    def teste_metodo_nao_exposto_e_recusado(self):
        cliente = self._cliente()
        with self.assertRaises(ErroRemotoRMI):
            cliente.urna.servico()

    def teste_login_invalido(self):
        cliente = ClienteRMI("kleyton", "senha errada", porta=self.porta)
        self.assertFalse(cliente.entrar())

    def teste_callback_entrega_nota_a_todos(self):
        um = self._cliente("kleyton")
        dois = self._cliente("mariana")
        admin = self._cliente("admin", "admin")

        antes_um = len(um._receptor.recebidas)
        antes_dois = len(dois._receptor.recebidas)

        admin.painel.publicar("ALERTA", "teste de callback", "admin")
        time.sleep(0.8)

        self.assertGreater(len(um._receptor.recebidas), antes_um)
        self.assertGreater(len(dois._receptor.recebidas), antes_dois)
        recebida = um._receptor.recebidas[-1]
        self.assertIsInstance(recebida, NotaInformativa)
        self.assertIn("teste de callback", recebida.mensagem)

    def teste_cancelar_inscricao(self):
        cliente = self._cliente("joao")
        self.assertIn("joao", cliente.painel.inscritos())
        cliente.painel.cancelar_receptor("joao")
        self.assertNotIn("joao", cliente.painel.inscritos())

    def teste_chamadas_simultaneas(self):
        cliente = self._cliente("joao")
        resultados = []
        falhas = []

        def consultar():
            try:
                resultados.append(len(cliente.urna.listar_candidatos()))
            except Exception as erro:
                falhas.append(erro)

        threads = [threading.Thread(target=consultar) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(falhas, [], f"chamadas simultaneas falharam: {falhas}")
        self.assertEqual(len(resultados), 10)
        self.assertTrue(all(r == resultados[0] for r in resultados))

if __name__ == "__main__":
    unittest.main(verbosity=2)
