import socket
import sys
import threading
import time

PINGS = 10           # quantidade de pings a enviar
INTERVAL = 1.0       # intervalo entre pings, em segundos
TIMEOUT = 1.0        # tempo maximo de espera por uma resposta, em segundos


class PingClient:
    def __init__(self, host, port):
        self.addr = (host, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Ajusta o timeout do socket: se nao chegar nada em 1s, levanta excecao.
        self.sock.settimeout(TIMEOUT)

        self.send_times = {}   # seq -> instante de envio
        self.rtts = {}         # seq -> RTT em ms (apenas os respondidos)
        self.lock = threading.Lock()
        self.sent = 0

    # ---------- Exercicio 2: 1 ping por segundo, agendado por timer ----------
    def send_ping(self):
        seq = self.sent
        if seq >= PINGS:
            return

        now = time.time()
        # PING sequence_number time CRLF
        message = "PING {} {}\r\n".format(seq, now)

        with self.lock:
            self.send_times[seq] = now
        self.sock.sendto(message.encode('utf-8'), self.addr)
        print("Enviado:  PING {} {:.6f}".format(seq, now))

        self.sent += 1
        if self.sent < PINGS:
            # Agenda o proximo envio para daqui a 1 segundo, independente
            # de a resposta anterior ter chegado ou nao.
            t = threading.Timer(INTERVAL, self.send_ping)
            t.daemon = True
            t.start()

    def receive_loop(self):
        """Fica recebendo respostas ate acabar o tempo total do teste."""
        # Tempo total: envio dos 10 pings + 1s de tolerancia para o ultimo.
        deadline = time.time() + (PINGS - 1) * INTERVAL + TIMEOUT + 0.5

        while time.time() < deadline:
            try:
                data, _ = self.sock.recvfrom(1024)
            except socket.timeout:
                # Nenhuma resposta neste intervalo; continua ate o deadline.
                continue

            arrival = time.time()
            # strip('\x00') protege contra o servidor Java, que pode ecoar o
            # buffer de 1024 bytes com zeros no final.
            line = data.decode('utf-8', errors='replace').strip('\x00').strip()
            parts = line.split()
            if len(parts) < 3 or parts[0] != "PING":
                continue

            seq = int(parts[1])
            with self.lock:
                start = self.send_times.get(seq)
                if start is None or seq in self.rtts:
                    continue
                rtt = (arrival - start) * 1000.0   # em milissegundos
                self.rtts[seq] = rtt

            print("Resposta: seq={}  rtt={:.3f} ms".format(seq, rtt))

    def run(self):
        print("Enviando {} pings para {}:{}\n".format(PINGS, self.addr[0], self.addr[1]))
        self.send_ping()          # dispara o primeiro; os demais se agendam sozinhos
        self.receive_loop()
        self.report()
        self.sock.close()

    # ---------- Exercicio 1: estatisticas de RTT ----------
    def report(self):
        received = len(self.rtts)
        lost = PINGS - received
        loss_pct = (lost / PINGS) * 100.0

        print("\n--- {} estatisticas do ping UDP ---".format(self.addr[0]))
        print("{} pacotes transmitidos, {} recebidos, {:.1f}% de perda".format(
            PINGS, received, loss_pct))

        # Pacotes perdidos (nao responderam dentro do tempo).
        perdidos = sorted(set(range(PINGS)) - set(self.rtts))
        if perdidos:
            print("Sequencias perdidas: {}".format(
                ", ".join(str(s) for s in perdidos)))

        if received:
            valores = list(self.rtts.values())
            minimo = min(valores)
            maximo = max(valores)
            media = sum(valores) / received
            print("rtt min/avg/max = {:.3f}/{:.3f}/{:.3f} ms".format(minimo, media, maximo))
        else:
            print("Nenhuma resposta recebida - impossivel calcular RTT.")


def main():
    if len(sys.argv) != 3:
        print("Uso: python3 ping_client.py <host> <porta>")
        return
    PingClient(sys.argv[1], int(sys.argv[2])).run()


if __name__ == '__main__':
    main()