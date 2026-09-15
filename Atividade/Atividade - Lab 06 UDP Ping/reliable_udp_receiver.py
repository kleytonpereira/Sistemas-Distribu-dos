import random
import socket
import sys
import zlib

LOSS_RATE = 0.2          # 20% dos ACKs sao "perdidos" de proposito
BUFFER_SIZE = 2048
SEP = b'|'


def checksum(payload):
    return zlib.crc32(payload) & 0xffffffff


def parse(packet):
    """Divide o pacote em (tipo, seq, checksum, payload). None se malformado."""
    parts = packet.split(SEP, 3)
    if len(parts) < 4:
        return None
    try:
        return parts[0].decode(), int(parts[1]), int(parts[2]), parts[3]
    except (ValueError, UnicodeDecodeError):
        return None


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 reliable_udp_receiver.py <porta> [arquivo_de_saida]")
        return

    port = int(sys.argv[1])
    out_path = sys.argv[2] if len(sys.argv) > 2 else None

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', port))
    print("ReliableUdpReceiver escutando na porta {} (LOSS_RATE dos ACKs = {})"
          .format(port, LOSS_RATE))

    expected = 0            # numero de sequencia esperado (alterna 0/1)
    recebidos = bytearray()  # dados entregues a aplicacao

    while True:
        packet, addr = sock.recvfrom(BUFFER_SIZE)
        parsed = parse(packet)

        if parsed is None:
            print("[recv] pacote malformado, descartado")
            continue

        tipo, seq, chk, payload = parsed

        # Verificacao de integridade.
        if chk != checksum(payload):
            print("[recv] seq={} CORROMPIDO (checksum invalido), descartado".format(seq))
            continue

        if tipo == 'FIN':
            print("[recv] FIN recebido - encerrando")
            send_ack(sock, addr, seq, forcar=True)
            break

        if tipo != 'DATA':
            continue

        if seq == expected:
            recebidos.extend(payload)
            print("[recv] seq={} ACEITO ({} bytes): {!r}".format(
                seq, len(payload), payload[:40].decode('utf-8', 'replace')))
            send_ack(sock, addr, seq)
            expected = 1 - expected      # alterna 0 <-> 1
        else:
            # Duplicata: o ACK anterior se perdeu. Reenvia o ACK sem
            # entregar o dado de novo a aplicacao.
            print("[recv] seq={} DUPLICADO (esperava {}) - reenviando ACK".format(
                seq, expected))
            send_ack(sock, addr, seq)

    print("\n--- Transferencia concluida: {} bytes recebidos ---".format(len(recebidos)))
    texto = recebidos.decode('utf-8', 'replace')
    print(texto)

    if out_path:
        with open(out_path, 'wb') as f:
            f.write(recebidos)
        print("Gravado em {}".format(out_path))

    sock.close()


def send_ack(sock, addr, seq, forcar=False):
    """Envia ACK|<seq>, simulando perda de ACK na rede."""
    if not forcar and random.random() < LOSS_RATE:
        print("[recv] ACK {} PERDIDO (simulado)".format(seq))
        return
    payload = b''
    ack = SEP.join([b'ACK', str(seq).encode(), str(checksum(payload)).encode(), payload])
    sock.sendto(ack, addr)
    print("[recv] ACK {} enviado".format(seq))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nReceiver encerrado.")