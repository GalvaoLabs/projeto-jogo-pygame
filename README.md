# Startup Tycoon — Construa um Império

Jogo de gestão em pygame: contrate, lance produtos, faça marketing e leve sua startup a
R$ 1 milhão de patrimônio sem quebrar. 5 idiomas (pt-BR, en, es, fr, de), Dashboard + Escritório animado.

Plataformas: **navegador (itch.io)**, **Windows**, **macOS**, **Linux** e **Android**.

## Jogar / controles

| Ação | Mouse / toque | Teclado |
|---|---|---|
| Navegar | botões | `TAB` Dashboard ⇄ Escritório · `1`–`5` abas · `O` escritório |
| Encerrar mês | botão | `E` |
| Menu / voltar | botão Menu | `ESC` (Android: botão Voltar) |
| Tela cheia | Configurações | `F11` ou `Alt+Enter` |
| Som | Configurações | `M` |

O jogo salva sozinho (a cada mês, ao ir ao menu, a cada 20 s e ao sair/minimizar). **Continuar**
aparece no menu quando há um save. Onde ficam os dados: Windows `%APPDATA%\StartupTycoon`,
macOS `~/Library/Application Support/StartupTycoon`, Linux `~/.config/StartupTycoon`, Android
pasta privada do app, navegador `localStorage`.

## Rodar do código-fonte

```bash
pip install -r requirements.txt     # pygame-ce
python main.py
python -m unittest discover -s tests -v     # testes (funcionam com ou sem pygame instalado)
python tools/simulate.py                    # checagem de balanceamento (bots jogando 200 partidas)
```

## Publicar no itch.io (navegador)

```bash
python tools/build_web.py           # gera dist/startup-tycoon-itch.zip
```

Na página do jogo no itch.io — **confira nesta ordem**, é o que faz aparecer "Run game":

1. *Edit game → Kind of project* = **HTML**. (Se estiver em "Downloadable", o itch **nunca** oferece
   jogar no navegador, por melhor que seja o zip.)
2. *Uploads → Upload files* → envie `startup-tycoon-itch.zip`.
3. Marque **"This file will be played in the browser"** no arquivo enviado.
4. *Embed options*: *Viewport* **1280 × 720**, marque **Mobile friendly** (orientação *Landscape*),
   **Fullscreen button** e, se quiser, *Click to launch in fullscreen*.
5. Salve e abra a página (ou use *Draft* → ver como visitante). Na primeira vez o navegador baixa o
   runtime Python/WebAssembly do CDN do pygbag (alguns MB) e pede um clique para começar.

Requisito do itch: `index.html` na **raiz** do zip — o script confere isso (`verify`) antes de terminar.

Teste local do mesmo pacote: `cd dist/web && python -m http.server 8000` → http://localhost:8000
(precisa de internet para baixar o runtime do pygbag).

## Desktop (Windows / macOS / Linux)

PyInstaller não faz cross-compile: rode em cada sistema (ou deixe o GitHub Actions fazer).

```bash
pip install -r requirements-dev.txt
python tools/build_desktop.py       # gera dist/StartupTycoon-<sistema>-<arch>.zip|tar.gz
```

* Windows: pode aparecer o aviso do SmartScreen (app sem assinatura) → *Mais informações → Executar assim mesmo*.
* macOS: app sem assinatura/notarização → botão direito → *Abrir* na primeira vez.
* Linux: `tar xzf …; ./StartupTycoon/StartupTycoon`.

## Android

* Mais simples: o jogo roda no Chrome do Android via itch.io (botão de tela cheia).
* APK nativo: `pip install buildozer` e `buildozer android debug` (Linux/WSL; o primeiro build baixa
  SDK/NDK e demora). Troque `package.domain` no `buildozer.spec` antes de publicar na Play Store.
  O GitHub Actions também gera o APK (`android-apk`).

## CI / releases

`.github/workflows/build.yml`: testes → web, Windows, Linux, macOS (arm64 e Intel) e Android.
Ao dar push numa tag `vX.Y.Z` cria uma Release no GitHub e, se existir o secret `BUTLER_API_KEY`,
publica tudo no itch.io (ajuste `ITCH_TARGET` no topo do arquivo para `seu-usuario/seu-jogo`).

## Estrutura

```
main.py              ponto de entrada único (desktop, Android e web/pygbag)
game.py              loop, telas (menu/config/jogo/relatório/fim), save, atalhos
settings.py          constantes e balanceamento
core/                simulação (economia, empresa, funcionários, produto) — sem UI
modes/               Dashboard, Escritório (pixel art) e mini-toolkit de UI
systems/             localização, storage (arquivo/localStorage), áudio sintetizado, paths
locales/*.json       um arquivo por idioma (adicionar idioma = adicionar um JSON)
web/                 template do index.html (loader do pygbag corrigido)
tools/               build_web, build_desktop, make_icons, simulate
tests/               unitários + smoke test de todas as telas + "monkey test" de cliques
```

## Limitações conhecidas

* A interface é desenhada em 1280×720 e escalada. Em celulares pequenos os botões ficam menores
  do que o ideal para toque; um layout touch-first (botões maiores, rolagem por arrasto) é o próximo passo natural.
* Dificuldade única: uma estratégia focada em marketing vence em ~18 meses (`tools/simulate.py`).
  Níveis de dificuldade / modo desafio seriam o próximo passo de conteúdo.
