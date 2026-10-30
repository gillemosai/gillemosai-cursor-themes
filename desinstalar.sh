#!/usr/bin/env bash
# Gillemosai Cursor Themes - desinstalador (remove os temas e volta ao cursor padrão)
# https://gillemosai.com
set -euo pipefail

for destino in "$HOME/.local/share/icons" "$HOME/.icons"; do
  rm -rf "$destino"/Gillemosai_Cursor_*
done

if command -v gsettings >/dev/null 2>&1; then
  gsettings reset org.gnome.desktop.interface cursor-theme
  gsettings reset org.gnome.desktop.interface cursor-size
fi

# Restaura (ou remove) o fallback de X11 criado pelo instalador
if [ -f "$HOME/.icons/default/index.theme.bak-gillemosai" ]; then
  mv "$HOME/.icons/default/index.theme.bak-gillemosai" "$HOME/.icons/default/index.theme"
elif grep -q "Gillemosai_Cursor_" "$HOME/.icons/default/index.theme" 2>/dev/null; then
  rm -f "$HOME/.icons/default/index.theme"
fi

echo "Temas Gillemosai removidos. Saia da sessão e entre de novo se algum app ainda mostrar o cursor antigo."
