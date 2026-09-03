# Lab 06 — Pinger UDP

**Disciplina:** Redes e Sistemas Distribuídos — UFC Quixadá
**Professor:** Rafael Braga
**Aluno:** Kleyton Kluesriton Ferreira

> **Observação:** o servidor está em **Java**, como no roteiro. O cliente e as
> classes do exercício 3 estão em **Python**, conforme autorizado pelo professor
> para uso de outras linguagens. Como o protocolo é texto sobre UDP, os dois
> conversam sem problema — o servidor não interpreta a mensagem, apenas ecoa
> os bytes de volta.

## Arquivos

| Arquivo | O que é |
|---|---|
| `PingServer.java` | Servidor de Ping UDP em Java (versão do roteiro, corrigida) |
| `ping_client.py` | Cliente de Ping — 10 pings, timeout de 1s, **exercícios 1 e 2** |
| `reliable_udp_sender.py` | **Exercício 3** — remetente confiável sobre UDP |
| `reliable_udp_receiver.py` | **Exercício 3** — destinatário confiável sobre UDP |

---

## Como executar

### 1. Compilar o servidor (uma vez)

```bash
javac PingServer.java
```

### 2. Servidor e cliente — dois terminais

**Terminal 1 — servidor:**

```bash
java PingServer 12000
```

Se der erro de classe não encontrada: `java -classpath . PingServer 12000`

Deve aparecer:

```
PingServer escutando na porta 12000 (LOSS_RATE=0.3, AVERAGE_DELAY=100ms)
```

**Terminal 2 — cliente:**

```bash
python3 ping_client.py 127.0.0.1 12000
```

Use uma porta **maior que 1024**. Para testar com a máquina de um colega, troque
`127.0.0.1` pelo IP dele.

### 3. Exercício 3 — dois terminais

```bash
# terminal 1
python3 reliable_udp_receiver.py 13000

# terminal 2
python3 reliable_udp_sender.py 127.0.0.1 13000 "mensagem que quero enviar"
# ou:  python3 reliable_udp_sender.py 127.0.0.1 13000 --file arquivo.txt
```

---

## Saída de uma execução real

**Cliente:**

```
Enviado:  PING 0 1788395932.602936
Resposta: seq=0  rtt=179.621 ms
Enviado:  PING 1 1788395933.603741
Resposta: seq=1  rtt=58.108 ms
Enviado:  PING 2 1788395934.604661
...
--- 127.0.0.1 estatísticas do ping UDP ---
10 pacotes transmitidos, 8 recebidos, 20.0% de perda
Sequências perdidas: 2, 7
rtt min/avg/max = 13.036/91.227/179.621 ms
```

**Servidor:**

```
Received from 127.0.0.1:50942 -> PING 0 1788395932.602936
Reply sent.
Received from 127.0.0.1:50942 -> PING 2 1788395934.6046607
Reply not sent.
```

As linhas `Reply not sent.` do servidor correspondem exatamente às "Sequências
perdidas" do cliente — ou seja, o cliente só desistiu dos pacotes que o servidor
realmente descartou, o que confirma o timeout de 1s funcionando.

---

## Formato da mensagem

```
PING <sequence_number> <time> CRLF
```

`sequence_number` vai de 0 a 9; `time` é o instante do envio. O servidor devolve
os mesmos bytes sem modificação, e o cliente casa a resposta com o envio pelo
número de sequência para calcular o RTT.

---

## Correções feitas no `PingServer.java` do roteiro

O código do PDF não roda como está. Três correções foram necessárias:

1. **`new DatagramSocket(port)` estava dentro do `while`.** Na segunda volta do
   laço isso lança `BindException`, porque a porta já está em uso. A criação do
   socket (e a checagem de `args`) foi movida para fora do laço.
2. **`Thread.sleep((int)(random.nextDouble()) * 2 * AVERAGE_DELAY)`** — o cast
   `(int)` estava aplicado ao `nextDouble()`, que devolve algo entre 0 e 1;
   convertido para `int` isso é **sempre 0**, então o atraso simulado nunca
   acontecia. Corrigido para `(long)(random.nextDouble() * 2 * AVERAGE_DELAY)`.
3. **O eco devolvia os 1024 bytes do buffer inteiro**, com zeros depois da
   mensagem. Passou a usar `request.getLength()` no `DatagramPacket` de
   resposta, devolvendo apenas os bytes que chegaram.

---

## Exercícios

### 1) RTT mínimo, máximo e médio (fácil)

Implementado em `ping_client.py`, método `report()`.

O cliente guarda o instante de envio de cada sequência em `self.send_times` e,
quando a resposta chega, calcula `rtt = (chegada - envio) * 1000` em ms,
gravando em `self.rtts`. No fim imprime o resumo no formato do `ping` do
sistema, com mínimo, média e máximo, além do percentual de perda.

Só entram na média os pacotes que voltaram — pacote perdido não tem RTT, ele
entra na contagem de perda.

### 2) Exatamente 1 Ping por segundo (difícil)

Implementado em `ping_client.py` com `threading.Timer`, equivalente Python
direto das classes `Timer` / `TimerTask` do `java.util` citadas na dica.

No programa básico, envio e recepção ficam no mesmo laço, então o próximo ping
só sai depois que o anterior é respondido (ou dá timeout) — o intervalo real
vira *1s + RTT* e varia conforme a rede.

A solução separa as duas coisas em fluxos independentes:

- **Envio** — `send_ping()` dispara o pacote e, antes de retornar, agenda a si
  mesmo para daqui a 1 segundo (`threading.Timer(1.0, self.send_ping)`). O
  relógio de envio não depende de nada que chegue da rede.
- **Recepção** — `receive_loop()` roda em paralelo, com `settimeout(1.0)` no
  socket, casando cada resposta com seu envio pelo número de sequência.

Assim os pings saem em 1,000s / 2,000s / 3,000s… mesmo com respostas atrasadas
ou perdidas, como no `ping` do sistema operacional.

### 3) ReliableUdpSender e ReliableUdpReceiver (difícil)

Protocolo **stop-and-wait com número de sequência alternante (0/1)** — o rdt 3.0
do Kurose, base do que o TCP faz. Transporte unidirecional: só o remetente manda
dados, o destinatário só devolve acknowledgements.

**Formato do pacote:** `TIPO|seq|checksum|payload`, com `TIPO` em
`DATA` / `ACK` / `FIN` e checksum CRC32 do payload.

**Como a confiabilidade é obtida:**

1. O remetente envia `DATA|seq` e liga um temporizador (`TIMEOUT = 0.5s`).
2. Se o `ACK|seq` correto chega a tempo, ele alterna o seq e manda o próximo
   segmento.
3. Se o temporizador estoura — ou chega um ACK com seq errado/corrompido — ele
   **retransmite o mesmo segmento**. Isso cobre tanto a perda do dado quanto a
   perda do ACK.
4. O destinatário confere o checksum; pacote corrompido é descartado (o
   remetente retransmite por timeout).
5. Se chega um seq **duplicado** (sinal de que o ACK anterior se perdeu), o
   destinatário **não entrega o dado de novo** à aplicação, mas reenvia o ACK —
   é isso que destrava o remetente sem duplicar bytes no resultado final.
6. `FIN` encerra a transferência, também confirmado com ACK.

**Simulação de perda:** como o ambiente de teste (localhost) praticamente não
perde pacotes IP, a perda é injetada artificialmente — `LOSS_RATE = 0.3` no
sender descarta pacotes de dados e `LOSS_RATE = 0.2` no receiver descarta ACKs.
Zerando os dois, a transferência sai sem nenhuma retransmissão.

**Saída de uma execução real:**

```
[send] DATA seq=1 PERDIDO na rede (simulado)
[send] TIMEOUT esperando ACK 1 - retransmitindo
[send] DATA seq=1 enviado (tentativa 2)
[send] ACK 1 recebido -> segmento confirmado

--- Transferência concluída ---
135 bytes entregues em 7 segmentos, 4 retransmissões
```

O destinatário reconstrói a mensagem original completa e sem duplicações, mesmo
tendo havido perdas no meio — que é o ponto do exercício.

**Limitação conhecida:** stop-and-wait tem apenas 1 pacote em trânsito por vez,
então a vazão é limitada a `1 segmento / RTT`. A evolução natural seria
Go-Back-N ou repetição seletiva, com uma janela de N pacotes não confirmados.
