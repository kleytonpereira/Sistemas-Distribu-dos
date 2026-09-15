#!/usr/bin/env bash
# demo_trabalho2.sh — demonstração automática do Trabalho 2 (RMI).
#
# Mostra, em sequência: os objetos publicados, passagem por valor,
# passagem por referência, erro remoto e o callback substituindo o multicast.
set -u
cd "$(dirname "$0")"
python3 -m trabalho2_rmi.demonstracao
