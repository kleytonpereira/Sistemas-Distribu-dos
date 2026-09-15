# Lab 06 — Pinger UDP

**Disciplina:** Redes e Sistemas Distribuídos — UFC Quixadá
**Professor:** Rafael Braga
**Aluno:** Kleyton Kluesriton Ferreira

> **Observação:** o servidor está em **Java**, como no roteiro. O cliente e as
> classes do exercício 3 estão em **Python**, conforme autorizado pelo professor
> para uso de outras linguagens. Como o protocolo é texto sobre UDP, os dois
> conversam sem problema — o servidor não interpreta a mensagem, apenas ecoa os
> bytes de volta.

## Arquivos

| Arquivo | O que é |
|---|---|
| `PingServer.java` | Servidor de Ping UDP em Java (versão do roteiro, corrigida) |
| `ping_client.py` | Cliente de Ping — 10 pings, timeout de 1s, exercícios 1 e 2 |
| `reliable_udp_sender.py` | Exercício 3 — remetente confiável sobre UDP |
| `reliable_udp_receiver.py` | Exercício 3 — destinatário confiável sobre UDP |

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

Use uma porta maior que 1024. Para testar com a máquina de um colega, troque
`127.0.0.1` pelo IP dele.

### 3. Exercício 3 — dois terminais

```bash
# terminal 1
python3 reliable_udp_receiver.py 13000

# terminal 2
python3 reliable_udp_sender.py 127.0.0.1 13000 "mensagem que quero enviar"
# ou:  python3 reliable_udp_sender.py 127.0.0.1 13000 --file arquivo.txt
```
