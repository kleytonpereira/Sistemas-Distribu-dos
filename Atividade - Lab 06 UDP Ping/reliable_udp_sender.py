import random
import socket
import sys
import zlib

LOSS_RATE = 0.3          # 30% dos pacotes de dados sao "perdidos" de proposito
TIMEOUT = 0.5            # tempo de espera pelo ACK, em segundos
MAX_RETRIES = 20         # desiste depois disso (evita loop infinito)
CHUNK = 20               # bytes por segmento (pequeno, para ver o protocolo agir)
SEP = b'|'

MENSAGEM_PADRAO = (
    "Transferencia confiavel de dados sobre UDP usando stop-and-wait "
    "com numeros de sequencia, acknowledgements e retransmissao por timeout."
)


def checksum(payload):
    return zlib.crc32(payload) & 0xffffffff


def build(tipo, seq, payload):
    return SEP.join([tipo.encode(), str(seq).encode(),
                     str(checksum(payload)).encode(), payload])


class ReliableUdpSender:
    def __init__(self, host, port):
        self.addr = (host, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(TIMEOUT)
        self.seq = 0
        self.retransmissoes = 0

    def _enviar_com_confirmacao(self, tipo, payload):
        """Envia um pacote e so retorna quando o ACK correspondente chegar."""
        packet = build(tipo, self.seq, payload)

        for tentativa in range(1, MAX_RETRIES + 1):
            # Simula a perda do pacote de dados na rede: o remetente "acha"
            # que enviou, mas nada chega do outro lado.
            if random.random() < LOSS_RATE:
                print("[send] {} seq={} PERDIDO na rede (simulado)".format(tipo, self.seq))
            else:
                self.sock.sendto(packet, self.addr)
                print("[send] {} seq={} enviado (tentativa {})".format(
                    tipo, self.seq, tentativa))

            try:
                resposta, _ = self.sock.recvfrom(2048)
            except socket.timeout:
                print("[send] TIMEOUT esperando ACK {} - retransmitindo".format(self.seq))
                self.retransmissoes += 1
                continue

            parts = resposta.split(SEP, 3)
            if len(parts) < 4:
                self.retransmissoes += 1
                continue

            tipo_r, seq_r = parts[0].decode(), int(parts[1])
            if tipo_r == 'ACK' and seq_r == self.seq:
                print("[send] ACK {} recebido -> segmento confirmado".format(seq_r))
                self.seq = 1 - self.seq      # alterna 0 <-> 1
                return True

            print("[send] ACK inesperado ({} {}) - retransmitindo".format(tipo_r, seq_r))
            self.retransmissoes += 1

        print("[send] FALHA: excedido o numero maximo de tentativas.")
        return False

    def enviar(self, dados):
        total = len(dados)
        segmentos = [dados[i:i + CHUNK] for i in range(0, total, CHUNK)]
        print("Enviando {} bytes em {} segmentos para {}:{}\n".format(
            total, len(segmentos), self.addr[0], self.addr[1]))

        for seg in segmentos:
            if not self._enviar_com_confirmacao('DATA', seg):
                return

        self._enviar_com_confirmacao('FIN', b'')

        print("\n--- Transferencia concluida ---")
        print("{} bytes entregues em {} segmentos, {} retransmissoes".format(
            total, len(segmentos), self.retransmissoes))
        self.sock.close()


def main():
    if len(sys.argv) < 3:
        print('Uso: python3 reliable_udp_sender.py <host> <porta> ["mensagem"]')
        print('     python3 reliable_udp_sender.py <host> <porta> --file arquivo.txt')
        return

    host, port = sys.argv[1], int(sys.argv[2])

    if len(sys.argv) >= 5 and sys.argv[3] == '--file':
        with open(sys.argv[4], 'rb') as f:
            dados = f.read()
    elif len(sys.argv) >= 4:
        dados = sys.argv[3].encode('utf-8')
    else:
        dados = MENSAGEM_PADRAO.encode('utf-8')

    ReliableUdpSender(host, port).enviar(dados)


if __name__ == '__main__':
    main()