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
```

### Controles
| Entrada | Ação |
| --- | --- |
| Mouse | Clicar em botões, funcionários e objetos do escritório |
| `TAB` ou botões DASHBOARD / ESCRITÓRIO | Alternar interface |
| ENCERRAR MÊS | Roda a simulação mensal e mostra o relatório |
| `Enter` / `Espaço` / `Esc` | Fechar o relatório |
| `Esc` | Abrir o menu (Continuar volta ao jogo); em Configurações volta ao menu |

### Como gerar o executável (Windows)
```
pip install -r requirements.txt -r requirements-dev.txt
pyinstaller startup_tycoon.spec --noconfirm
```
Resultado: `dist/StartupTycoon/StartupTycoon.exe` (distribua a pasta inteira, ou use `tools/build_windows.bat`,
que também roda os testes e gera o zip). Os JSON de idiomas e as fontes são incluídos no pacote.
> ⚠️ A configuração do PyInstaller foi escrita mas **ainda não foi executada** (veja “Situação”).

### Versão web
Preparada, **não testada em navegador**. Análise, riscos e checklist em [`docs/WEB.md`](docs/WEB.md).

### Adicionar um idioma
1. Copie `locales/en_US.json` para `locales/xx_XX.json` e traduza `strings` e `meta` (formato de número, moeda, data, meses).
2. Pronto — nenhum código muda. O idioma só aparece no seletor quando **todas** as chaves de `pt_BR.json` estão presentes e não vazias.
   Use `"status": "beta"` para exibir a etiqueta *beta* ou `"status": "draft"` para escondê-lo.
3. Rode os testes (`python -m unittest discover -s tests`).

### Arquitetura
```
STARTUP-TYCOON/
├── main.py              ponto de entrada (loop assíncrono: desktop e web)
├── game.py              loop, menu, configurações, relatório, vitória/falência
├── settings.py          constantes e números de balanceamento
├── core/                economia e estado da empresa (sem texto de interface)
│   ├── company.py       ações devolvem (ok, Msg): chave de tradução + números
│   ├── economy.py · employee.py · product.py
├── modes/               dashboard.py · office.py · ui.py (toolkit imediato, fontes, ajuste de texto)
├── systems/
│   ├── localization.py  t(), tu(), tn(), money(), formatação regional, fallback
│   ├── settings_manager.py  settings.json (idioma, tela cheia, volume) à prova de arquivo corrompido
│   ├── paths.py         caminhos em desenvolvimento / PyInstaller / web
│   └── time_system.py
├── locales/             pt_BR · en_US · es_ES · fr_FR · de_DE (.json)
├── assets/fonts/        DejaVu Sans Condensed (acentos, ç, ñ, ß, €)
├── tests/               test_i18n.py · test_ui_languages.py · smoke_ui.py · simulate.py
├── tools/               build_windows.bat · build_web.sh · take_screenshots.py
├── docs/                WEB.md · itch/page.md
└── startup_tycoon.spec  configuração do PyInstaller
```
A economia trabalha só com números; o texto é montado na interface a partir de `Msg(chave, parâmetros)`.
Por isso trocar de idioma reconstrói tudo (inclusive avisos ainda na tela) sem tocar na partida.
Configurações ficam em `%APPDATA%\StartupTycoon\settings.json` (Windows), `~/.config/StartupTycoon/` (Linux)
ou `~/Library/Application Support/StartupTycoon/` (macOS); defina `STARTUP_TYCOON_CONFIG_DIR` para mudar.

### Testes
```
python -m unittest discover -s tests -v   # i18n, formatação, persistência, layout de todas as telas × 5 idiomas
python tests/smoke_ui.py                  # roteiro de cliques pelo jogo real
python tests/simulate.py                  # balanceamento da economia com bots
```
Sem o pygame instalado, os testes usam um substituto **apenas de desenvolvimento** baseado em Pillow
(`tests/support`); isso não valida pygame real. Instale `pygame` e rode de novo para a validação definitiva.

### Screenshots
Ainda não há screenshots no repositório. Gere os reais com `python tools/take_screenshots.py` (pygame real).

### Limitações conhecidas
- Janela fixa de 1280 × 720 (tela cheia escala a imagem).
- Sem som e sem jogos salvos; o controle de volume do `settings.json` ainda não é usado.
- Símbolo da moeda muda com o idioma (R$, $, €) **somente na exibição**: não há conversão cambial.
- Francês e alemão sem revisão de falantes nativos. Nomes dos funcionários são sempre os mesmos.
- Versão web e executável Windows: preparados, não testados (ver acima).
- Texto longo demais é reduzido ou cortado com “…” em vez de quebrar o layout.

---

## English

A 2D business-management simulation in Python + Pygame. Run a tech startup: hire a team, build and price
your product, invest in marketing and reach **R$ 1,000,000 net worth** before you run out of cash.
Two interfaces share one simulation: an **Executive Dashboard** and a pixel-art **Office**.

**Languages:** Português (Brasil, default), English, Español — complete. Français, Deutsch — complete but *beta*
(no native-speaker review). Switch any time from Menu → Settings; the match is not restarted and the choice is saved.
Numbers, currency and dates follow the language; game values never change. The currency symbol is display-only (no exchange rate).

**Install & run** (Python 3.9+)
```
pip install -r requirements.txt
python main.py
```
**Controls:** mouse for everything · `TAB` switches Dashboard/Office · `Esc` opens the menu / closes the report.

**Build the Windows executable:** `pip install -r requirements-dev.txt` then `pyinstaller startup_tycoon.spec --noconfirm`
→ `dist/StartupTycoon/StartupTycoon.exe` (not yet run — see Status below).

**Web build (Pygbag):** prepared but untested in a browser — see [`docs/WEB.md`](docs/WEB.md).

**Tests:** `python -m unittest discover -s tests -v` · `python tests/smoke_ui.py` · `python tests/simulate.py`.
Without pygame installed they run on a development-only Pillow stand-in (not a real-pygame validation).

**Add a language:** copy `locales/en_US.json` to `locales/xx_XX.json`, translate `strings` and `meta`; it appears in the picker once every key of `pt_BR.json` is present.

**Screenshots:** none committed yet; generate real ones with `python tools/take_screenshots.py`.

---

## Situação / Status
| Item | Estado |
| --- | --- |
| i18n (5 idiomas), seletor, persistência, formatação regional | Implementado e testado (pygame substituto) |
| Renderização com pygame real | **Não testada** |
| Executável Windows (PyInstaller) | Implementado, **não testado** |
| Versão web (Pygbag) | Parcial, **não testada** |
