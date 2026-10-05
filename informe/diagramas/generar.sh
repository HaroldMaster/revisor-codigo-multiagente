#!/bin/bash
# Genera las imágenes de los diagramas del informe a partir de los .mmd (Mermaid).
cd "$(dirname "$0")"
for d in bucle baseline multiagente devcycle; do
  npx -y @mermaid-js/mermaid-cli -p chrome.json -i $d.mmd -o $d.png -w 2400 -s 2 -b white
done
