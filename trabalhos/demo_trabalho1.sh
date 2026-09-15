#!/usr/bin/env bash
# demo.sh — roteiro de demonstração do Trabalho 1.
#
# Roda em sequência tudo o que não precisa de dois terminais: questões 1b,
# 1c, 2b, 2c, os testes automatizados e, para 1d/2d/3, sobe o servidor em
# segundo plano automaticamente.
#
# Uso:  ./demo.sh          (da raiz do projeto)

set -u
cd "$(dirname "$0")"

titulo() { printf '\n\033[1;34m=== %s ===\033[0m\n' "$1"; }

titulo "T1 Questão 1b — OutputStream -> saída padrão"
python3 -m trabalho1_votacao.questao1_output_stream.teste_b_saida_padrao

titulo "Questão 1c — OutputStream -> arquivo"
python3 -m trabalho1_votacao.questao1_output_stream.teste_c_arquivo

titulo "Questão 2c — InputStream <- arquivo"
python3 -m trabalho1_votacao.questao2_input_stream.teste_c_arquivo

titulo "Questões 1b+2b encadeadas por pipe (stdout -> stdin)"
python3 -m trabalho1_votacao.questao2_input_stream.gerar_bytes_puros \
  | python3 -m trabalho1_votacao.questao2_input_stream.teste_b_entrada_padrao

titulo "Questão 1d — OutputStream -> servidor remoto TCP"
python3 -u -m trabalho1_votacao.questao1_output_stream.servidor_coletor_tcp & SRV=$!
sleep 1
python3 -m trabalho1_votacao.questao1_output_stream.teste_d_cliente_tcp
sleep 1; kill $SRV 2>/dev/null; wait $SRV 2>/dev/null

titulo "Questão 2d — InputStream <- cliente remoto TCP"
python3 -u -m trabalho1_votacao.questao2_input_stream.servidor_decodificador_tcp & SRV=$!
sleep 1
python3 -m trabalho1_votacao.questao2_input_stream.teste_d_cliente_tcp
sleep 1; kill $SRV 2>/dev/null; wait $SRV 2>/dev/null

titulo "Questão 3 — serialização cliente-servidor"
python3 -u -m trabalho1_votacao.questao3_serializacao.servidor & SRV=$!
sleep 1
python3 -m trabalho1_votacao.questao3_serializacao.cliente
sleep 1; kill $SRV 2>/dev/null; wait $SRV 2>/dev/null

titulo "Testes automatizados"
python3 -m unittest discover -s trabalho1_votacao/testes -t . 2>&1 | tail -5

titulo "Falta demonstrar ao vivo (precisam de vários terminais)"
cat <<'FIM'
  Questão 4 (multicast):
    terminal 1: python3 -m trabalho1_votacao.questao4_multicast.servidor
    terminal 2: python3 -m trabalho1_votacao.questao4_multicast.cliente kleyton 123
    terminal 3: python3 -m trabalho1_votacao.questao4_multicast.cliente mariana 123

  Questão 6 (votação completa):
    terminal 1: python3 -m trabalho1_votacao.questao6_extra_votacao.servidor 120
    terminal 2: python3 -m trabalho1_votacao.questao6_extra_votacao.cliente_eleitor kleyton 123
    terminal 3: python3 -m trabalho1_votacao.questao6_extra_votacao.cliente_eleitor mariana 123
    terminal 4: python3 -m trabalho1_votacao.questao6_extra_votacao.cliente_admin admin admin
FIM
