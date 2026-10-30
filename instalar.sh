#!/usr/bin/env bash
# Gillemosai Cursor Themes - instalador para Linux (GNOME / Zorin OS / Ubuntu e derivados)
# https://gillemosai.com
#
# Uso:  ./instalar.sh <tema> <variante> [tamanho]
# Ex.:  ./instalar.sh base Dark 72
#       ./instalar.sh galaxy blue 96
#
# Sem argumentos, mostra a lista de temas e variantes.
set -euo pipefail

AQUI="$(cd "$(dirname "$0")" && pwd)"
ICONES=("$HOME/.local/share/icons" "$HOME/.icons")

listar() {
  cat <<'EOF'
Gillemosai Cursor Themes  -  https://gillemosai.com

Uso:  ./instalar.sh <tema> <variante> [tamanho]

Temas e variantes:
  base      Dark | Light          Seta delta com contorno laranja
  pixel8    White | Mint          Clima de plataforma retrô em 8 bits
  galaxy    Blue | Red            Neon de saga espacial, lâminas de energia
  hologram  Cyan | Amber          Painel holográfico de exploração espacial
  ninja     Orange | Blue         Kunai e shuriken em aço e laranja

Tamanho (px): padrão 72 (3x o cursor tradicional). Sugestões: 48, 72, 96, 128.
              No pixel8 use múltiplos de 24 (24, 48, 72, 96, 120) para pixels perfeitos.

Exemplos:
  ./instalar.sh base Dark 72
  ./instalar.sh galaxy Blue 96
EOF
}

if [ $# -lt 2 ]; then
  listar
  exit 0
fi

TEMA_IN="${1,,}"
VAR_IN="${2,,}"
TAMANHO="${3:-72}"

case "$TEMA_IN" in
  base)     TEMA="base";     VARS=(Dark Light) ;;
  pixel8)   TEMA="Pixel8";   VARS=(White Mint) ;;
  galaxy)   TEMA="Galaxy";   VARS=(Blue Red) ;;
  hologram) TEMA="Hologram"; VARS=(Cyan Amber) ;;
  ninja)    TEMA="Ninja";    VARS=(Orange Blue) ;;
  *) echo "Tema desconhecido: '$1'." >&2; echo >&2; listar >&2; exit 1 ;;
esac

VAR=""
OUTRA=""
for v in "${VARS[@]}"; do
  if [ "${v,,}" = "$VAR_IN" ]; then VAR="$v"; else OUTRA="$v"; fi
done
if [ -z "$VAR" ]; then
  echo "Variante desconhecida: '$2'. Para '$TEMA' use: ${VARS[*]}" >&2
  exit 1
fi

if ! [[ "$TAMANHO" =~ ^[0-9]+$ ]] || [ "$TAMANHO" -lt 16 ] || [ "$TAMANHO" -gt 256 ]; then
  echo "Tamanho inválido: '$TAMANHO'. Use um número entre 16 e 256 (ex.: 72)." >&2
  exit 1
fi
if [ "$TEMA" = "Pixel8" ] && [ $((TAMANHO % 24)) -ne 0 ]; then
  echo "Aviso: para pixels perfeitos no Pixel8 use múltiplos de 24 (24, 48, 72, 96, 120)."
fi

PACOTE="$AQUI/dist/Gillemosai_Cursor_${TEMA}.tar.gz"
if [ ! -f "$PACOTE" ]; then
  echo "Pacote não encontrado: $PACOTE" >&2
  echo "Baixe o repositório completo (Code > Download ZIP) e rode o script de dentro da pasta." >&2
  exit 1
fi

NOME="Gillemosai_Cursor_${TEMA}-${VAR}"
NOME_OUTRA="Gillemosai_Cursor_${TEMA}-${OUTRA}"

# Instala as duas variantes do tema (tar preserva os atalhos de cursores)
for destino in "${ICONES[@]}"; do
  mkdir -p "$destino"
  rm -rf "$destino/Gillemosai_Cursor_${TEMA}-"*
  tar -xzf "$PACOTE" -C "$destino"
done

# Aplica no GNOME/Zorin. Alterna rapidamente para a outra variante e volta,
# para forçar o sistema a recarregar o desenho.
if command -v gsettings >/dev/null 2>&1; then
  gsettings set org.gnome.desktop.interface cursor-theme "$NOME_OUTRA"
  sleep 1
  gsettings set org.gnome.desktop.interface cursor-theme "$NOME"
  gsettings set org.gnome.desktop.interface cursor-size "$TAMANHO"
else
  echo "gsettings não encontrado: escolha o tema '$NOME' nas configurações de aparência do seu ambiente."
fi

# Fallback para apps que ignoram o gsettings (X11 puro, Qt, etc.)
mkdir -p "$HOME/.icons/default"
if [ -f "$HOME/.icons/default/index.theme" ] && [ ! -f "$HOME/.icons/default/index.theme.bak-gillemosai" ]; then
  cp "$HOME/.icons/default/index.theme" "$HOME/.icons/default/index.theme.bak-gillemosai"
fi
printf '[Icon Theme]\nInherits=%s\n' "$NOME" > "$HOME/.icons/default/index.theme"

echo "Pronto! Tema '$NOME' aplicado com cursor de ${TAMANHO}px."
echo "Se algum app ainda mostrar o cursor antigo, saia da sessão e entre de novo."
echo
echo "Mudar só o tamanho:  gsettings set org.gnome.desktop.interface cursor-size 96"
echo "Remover tudo:        ./desinstalar.sh"
echo "Mais temas em:       https://gillemosai.com"
