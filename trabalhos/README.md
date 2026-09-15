# QXD0043 — Sistemas Distribuídos · Trabalhos

UFC Quixadá · Prof. Antonio Rafael Braga
**Serviço remoto usado nos quatro trabalhos:** sistema de votação
**Linguagem:** Python 3.10+ (só biblioteca padrão)

Todos os comandos rodam **da raiz desta árvore** (esta pasta), com `python3 -m`.

```bash
python3 -m trabalho1_votacao.questao3_serializacao.servidor
```

## Estrutura

```
comum/                      compartilhado por todos os trabalhos
├── core/                     entidades e regras de negócio (não conhece rede)
├── sockets/                  TCP e multicast (não conhece votação)
└── rmi/                      invocação de método remoto (não conhece votação)

trabalho1_votacao/          T1 — comunicação entre processos (sockets)
trabalho2_rmi/              T2 — RPC / RMI (sem sockets)
```

## Trabalho 1 — Comunicação entre processos

Comandos em [`trabalho1_votacao/README.md`](trabalho1_votacao/README.md).

```bash
./demo_trabalho1.sh
```

## Trabalho 2 — RPC / RMI

Comandos em [`trabalho2_rmi/README.md`](trabalho2_rmi/README.md).

```bash
./demo_trabalho2.sh
```

## Testes

```bash
python3 -m unittest discover -s trabalho1_votacao/testes -t .
python3 -m unittest discover -s trabalho2_rmi/testes -t .
```

## Usuários de exemplo

Eleitores `kleyton`, `mariana`, `joao` (senha `123`) · administrador `admin` (senha `admin`).
