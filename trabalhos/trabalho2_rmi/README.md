# Trabalho 2 — RPC / RMI

Reimplementação da 4ª questão do Trabalho 1 usando invocação de método remoto,
com o protocolo requisição-resposta da seção 5.2. **Nenhum socket é criado.**

## Como executar

```bash
python3 -m trabalho2_rmi.servidor                     # terminal 1
python3 -m trabalho2_rmi.cliente_eleitor kleyton 123  # terminal 2
python3 -m trabalho2_rmi.cliente_eleitor mariana 123  # terminal 3
python3 -m trabalho2_rmi.cliente_admin admin admin    # terminal 4
```

Prazo da votação em segundos: `python3 -m trabalho2_rmi.servidor 60`.

Publique uma nota pelo cliente admin (opção 3) e ela aparece sozinha nos
terminais dos eleitores.

## Demonstração automática

```bash
./demo_trabalho2.sh
```

Percorre num processo só: objetos publicados, passagem por valor, passagem por
referência, erro remoto e o callback substituindo o multicast.

## Testes

```bash
python3 -m unittest discover -s trabalho2_rmi/testes -t .
```

## Onde cada exigência foi atendida

| Exigência | Onde |
|-----------|------|
| RPC/RMI, sem sockets | `comum/rmi/transporte.py` — XML-RPC da biblioteca padrão |
| `doOperation` | `comum/rmi/transporte.py::Transporte.doOperation` |
| `getRequest` | `comum/rmi/transporte.py::getRequest` |
| `sendReply` | `comum/rmi/transporte.py::sendReply` |
| mensagem como na figura | `comum/rmi/mensagem.py::Mensagem` |
| `objectReference` / `methodId` como String | nome registrado do objeto e nome do método |
| ≥4 classes entidade | `comum/core/pojos.py` — 6 classes |
| ≥2 agregação ("tem-um") | `Voto` tem-um `Candidato` e tem-um `Eleitor` |
| ≥2 extensão ("é-um") | `Eleitor` é-uma `Pessoa`; `Administrador` é-uma `Pessoa` |
| ≥4 métodos remotos | 15 ao todo |
| passagem por referência | `auth.login()` → `SessaoEleitor`; `sessao.urna()` → `ServicoVotacaoRemoto` |
| passagem por valor | `urna.listar_candidatos()`, `urna.apurar()`, `painel.historico()` |
| representação externa de dados | JSON UTF-8 em `comum/rmi/mensagem.py` |

## Objetos remotos

| Objeto | Nome registrado | Métodos remotos |
|--------|-----------------|-----------------|
| `ServicoAutenticacaoRemoto` | `auth` | `login`, `quem_esta_logado` |
| `ServicoVotacaoRemoto` | `votacao` | `listar_candidatos`, `segundos_restantes`, `apurar`, `adicionar_candidato`, `remover_candidato` |
| `PainelDeNotas` | `painel` | `registrar_receptor`, `cancelar_receptor`, `inscritos`, `historico`, `publicar` |
| `SessaoEleitor` | `sessaoeleitor#N` | `quem_sou`, `e_administrador`, `votar`, `ja_votei`, `urna` |
| `ReceptorDeNotas` *(no cliente)* | `receptor-<login>` | `receber_nota` |

## Referência x valor

```
herda de ObjetoRemoto   →  por REFERÊNCIA  (fica no servidor, cliente recebe proxy)
qualquer outro objeto   →  por VALOR       (serializado em JSON, cliente recebe cópia)
```

Mesma distinção do Java RMI entre `Remote` e `Serializable`.

- `listar_candidatos()` devolve **cópias** — alterar `candidato.votos` no cliente
  não muda o servidor.
- `sessao.votar(13)` roda **no servidor**, sobre o eleitor preso àquela sessão.

## Como o multicast virou callback

| Trabalho 1 (multicast) | Trabalho 2 (RMI) |
|---|---|
| `joinGroup` | cliente registra no `PainelDeNotas` a referência de um objeto seu |
| datagrama ao grupo | servidor invoca `receber_nota()` em cada referência registrada |
| `leaveGroup` | `cancelar_receptor` |
| ninguém sabe quem ouve | servidor mantém a lista e a limpa quando um cliente some |

O cliente também sobe um `ServidorRMI` — em RMI os dois lados hospedam objetos.
Cada callback sai numa thread própria.

## Estrutura

```
comum/rmi/                   infraestrutura (não conhece votação)
├── referencia.py              RemoteObjectRef
├── mensagem.py                a mensagem da figura + representação externa
├── transporte.py              doOperation / getRequest / sendReply
├── objeto_remoto.py           ObjetoRemoto e @metodo_remoto
├── proxy.py                   ProxyRemoto (stub do cliente)
└── servidor_rmi.py            registro, despachante e esqueleto

trabalho2_rmi/
├── objetos_remotos.py         objetos do domínio publicados
├── servidor.py
├── cliente_base.py
├── cliente_eleitor.py
├── cliente_admin.py
└── demonstracao.py
```

## Sobre "não crie sockets"

`comum/rmi/transporte.py` usa `xmlrpc.client` e `xmlrpc.server`, da biblioteca
padrão. Nenhuma linha do projeto chama `socket.socket()` — quem abre conexão é a
biblioteca, que é o "RPC pronto" que o enunciado permite. O protocolo
requisição-resposta do livro foi implementado **por cima** dele.
