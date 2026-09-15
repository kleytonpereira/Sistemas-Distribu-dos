# Trabalho 1 — Comunicação entre Processos (Capítulo 4)

**Serviço remoto:** sistema de votação. Comandos rodam da raiz da árvore (`../`).

## Questão 1 — `OutputStream`

```bash
python3 -m trabalho1_votacao.questao1_output_stream.teste_b_saida_padrao   # (b) saída padrão
python3 -m trabalho1_votacao.questao1_output_stream.teste_c_arquivo        # (c) arquivo

# (d) servidor remoto TCP — dois terminais
python3 -m trabalho1_votacao.questao1_output_stream.servidor_coletor_tcp
python3 -m trabalho1_votacao.questao1_output_stream.teste_d_cliente_tcp
```

## Questão 2 — `InputStream`

```bash
# (b) entrada padrão
python3 -m trabalho1_votacao.questao2_input_stream.gerar_bytes_puros \
  | python3 -m trabalho1_votacao.questao2_input_stream.teste_b_entrada_padrao

python3 -m trabalho1_votacao.questao2_input_stream.teste_c_arquivo         # (c) arquivo (rode o 1c antes)

# (d) cliente remoto TCP — dois terminais
python3 -m trabalho1_votacao.questao2_input_stream.servidor_decodificador_tcp
python3 -m trabalho1_votacao.questao2_input_stream.teste_d_cliente_tcp
```

## Questão 3 — Serialização cliente-servidor

```bash
python3 -m trabalho1_votacao.questao3_serializacao.servidor                # terminal 1
python3 -m trabalho1_votacao.questao3_serializacao.cliente                 # terminal 2
python3 -m trabalho1_votacao.questao3_serializacao.cliente --interativo    # menu
```

## Questão 4 — Multicast

```bash
python3 -m trabalho1_votacao.questao4_multicast.servidor                   # terminal 1
python3 -m trabalho1_votacao.questao4_multicast.cliente kleyton 123        # terminal 2
python3 -m trabalho1_votacao.questao4_multicast.cliente mariana 123        # terminal 3
```

Comandos do servidor: `n <msg>` · `a <msg>` · `u <msg>` · `auto` · `quem` · `sair`.

## Questão 6 (extra) — Votação completa

```bash
python3 -m trabalho1_votacao.questao6_extra_votacao.servidor 120                 # terminal 1 (prazo)
python3 -m trabalho1_votacao.questao6_extra_votacao.cliente_eleitor kleyton 123  # terminal 2
python3 -m trabalho1_votacao.questao6_extra_votacao.cliente_eleitor mariana 123  # terminal 3
python3 -m trabalho1_votacao.questao6_extra_votacao.cliente_admin admin admin    # terminal 4
```

## Testes

27 testes (serialização, regras de negócio, concorrência e rede). O enunciado não os exige.

```bash
python3 -m unittest discover -s trabalho1_votacao/testes -t .          # todos
python3 -m unittest discover -s trabalho1_votacao/testes -t . -v       # com nomes
python3 -m unittest trabalho1_votacao.testes.teste_tudo.TesteStreams   # só uma classe
```

O teste de multicast é pulado automaticamente em máquina sem suporte a multicast.

## Onde cada item do enunciado foi atendido

| Item | Exigência | Onde |
|------|-----------|------|
| — | ≥2 POJOs e ≥2 classes de serviço | `comum/core/pojos.py` (6), `comum/core/servicos.py` (2) |
| 1a | construtor com destino, array e quantidade | `CandidatoOutputStream.__init__` |
| 1b / 1c / 1d | `System.out` / arquivo / servidor TCP | `questao1_output_stream/teste_*` |
| 2a | construtor com `InputStream` de origem | `CandidatoInputStream.__init__` |
| 2b / 2c / 2d | `System.in` / arquivo / cliente TCP | `questao2_input_stream/teste_*` |
| 3a | empacotar/desempacotar nos dois lados | `comum/sockets/cliente_tcp.py`, `comum/sockets/servidor_tcp.py` |
| 4a | IP classe D + porta fixa, join/leaveGroup | `questao4_multicast/configuracao.py`, `comum/sockets/multicast.py` |
| 4b | NOTIFICAÇÃO / ALERTA / ATUALIZAÇÃO em JSON | `comum/core/pojos.py::NotaInformativa` |
| 4c | vários clientes em tempo real | rode `questao4_multicast.cliente` em vários terminais |
| 4d | 2 threads no cliente; servidor concorrente | `OuvinteMulticast`; comando `auto` no servidor |
| 4e | TCP autentica, UDP envia | `questao4_multicast/servidor.py` |
| 6 | votação com prazo, login e apuração | `questao6_extra_votacao/` |

## Se o multicast falhar

Exige interface de rede com suporte a multicast (falha em container ou VM isolada):

```bash
ip -4 addr show | grep inet
SD_INTERFACE=192.168.0.15 python3 -m trabalho1_votacao.questao4_multicast.servidor
```
