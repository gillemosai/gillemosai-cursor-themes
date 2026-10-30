# 🖱️ Gillemosai Cursor Themes

**Temas de cursor grandes e estilosos para Linux**, feitos para quem grava tutoriais, faz lives e quer um mouse que o público realmente enxergue.

5 temas · 10 variantes · 22 cursores cada · animações · tamanho padrão **72 px (3x o cursor tradicional)**, com opções até 128 px.

🌐 Criado por [**Gillemosai**](https://gillemosai.com) · mais projetos em **[gillemosai.com](https://gillemosai.com)**

---

## 🎨 Os temas

| Tema | Variantes | Estilo |
|---|---|---|
| **Gillemosai_Cursor_base** | Dark · Light | Seta delta com contorno laranja |
| **Gillemosai_Cursor_Pixel8** | White · Mint | Clima de plataforma retrô em 8 bits, com moeda girando no carregando |
| **Gillemosai_Cursor_Galaxy** | Blue · Red | Neon de saga espacial, com naves originais orbitando no carregando e voando no progresso |
| **Gillemosai_Cursor_Hologram** | Cyan · Amber | Painel holográfico de exploração espacial, com radar no carregando |
| **Gillemosai_Cursor_Ninja** | Orange · Blue | Kunai e shuriken em aço, com shuriken girando no carregando |

### Prévias

**Base**
![Base](docs/preview-base.png)

**Pixel8**
![Pixel8](docs/preview-Pixel8.png)

**Galaxy**
![Galaxy](docs/preview-Galaxy.png)

**Hologram**
![Hologram](docs/preview-Hologram.png)

**Ninja**
![Ninja](docs/preview-Ninja.png)

---

## 📥 Instalação (Zorin OS, Ubuntu, GNOME e derivados)

1. Baixe o projeto: botão verde **Code → Download ZIP** (ou use `git clone`) e extraia.
2. Abra o terminal dentro da pasta extraída.
3. Rode o instalador com o tema, a variante e (opcional) o tamanho:

```bash
./instalar.sh <tema> <variante> [tamanho]
```

Exemplos:

```bash
./instalar.sh base Dark 72        # seta delta, 3x o tamanho tradicional
./instalar.sh galaxy Blue 96      # neon azul, 4x
./instalar.sh pixel8 White 72     # 8 bits
./instalar.sh hologram Cyan 72
./instalar.sh ninja Orange 96
```

Rode `./instalar.sh` sem argumentos para ver a lista completa de temas e variantes.

Se algum aplicativo ainda mostrar o cursor antigo, **saia da sessão e entre de novo**.

> Se o script não executar, dê permissão: `chmod +x instalar.sh desinstalar.sh`

### Mudar só o tamanho

```bash
gsettings set org.gnome.desktop.interface cursor-size 96
```

Tamanhos incluídos: **24, 48, 72, 96 e 128** (no Pixel8: 24, 48, 72, 96 e 120, para manter os pixels perfeitos).

### Outros ambientes (KDE, XFCE, Cinnamon…)

O instalador copia os temas para `~/.local/share/icons` e `~/.icons`. Depois é só escolher o tema `Gillemosai_Cursor_...` nas configurações de cursor do seu ambiente.

### Desinstalar

```bash
./desinstalar.sh
```

Remove os temas Gillemosai e volta ao cursor padrão do sistema.

---

## 🧩 O que vem em cada tema

Seta, texto, texto vertical, mãozinha de clique, mão de arrastar (aberta e fechada), cruz, célula, mover, redimensionar nas 4 direções, proibido, ajuda, copiar, atalho, menu de contexto, zoom (mais e menos), **carregando e espera animados**, além de mais de 80 atalhos de nomes antigos e hashes, para o cursor funcionar em GTK, Qt, navegadores e apps legados.

## 🛠️ Gerar ou personalizar

Os cursores são desenhados em código (vetorial) e gerados em formato Xcursor:

```bash
pip install pillow
python3 src/make_themes.py
```

Os temas ficam em `build/` e os pacotes em `dist/`. Para criar o seu, edite as cores e os desenhos em `src/make_themes.py`.

---

## ℹ️ Sobre os temas

Os desenhos são **originais**, inspirados na estética de gêneros nerds (plataforma retrô, ficção espacial, ninja). Não usam personagens, logos ou marcas de nenhuma franquia, e este projeto não é afiliado a nenhuma delas.

## 📄 Licença

[MIT](LICENSE). Use, modifique e compartilhe, mantendo o crédito a **[Gillemosai](https://gillemosai.com)**.

---

## 🇬🇧 English (short)

Large, stylish cursor themes for Linux, made for tutorial creators. 5 themes, 10 variants, 22 cursors each, default size 72 px (3x the usual), up to 128 px. Install with `./instalar.sh <theme> <variant> [size]` (e.g. `./instalar.sh galaxy Blue 96`). Created by [Gillemosai](https://gillemosai.com).
