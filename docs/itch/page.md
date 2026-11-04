# itch.io — material de publicação (rascunho; NÃO publicado)

A publicação depende da conta e da autorização do proprietário. Nada foi enviado ao itch.io.

**Título:** STARTUP TYCOON — Build an Empire
**Tipo:** Downloadable (Windows). HTML5 só depois de testar `docs/WEB.md`.
**Gênero:** Simulation · **Tags:** tycoon, management, business, startup, economy, pixel-art, singleplayer, pygame, portuguese, spanish
**Idiomas:** Português (Brasil), English, Español — completos. Français e Deutsch — completos, marcados como beta (sem revisão de falantes nativos).

## Descrição curta
Simulador de gestão empresarial: contrate, desenvolva seu produto, invista em marketing e leve sua startup a R$ 1.000.000 de patrimônio antes que o caixa acabe.
_Short:_ A startup management sim — hire, build, market and grow your company to a million before the cash runs out.

## Descrição completa (EN)
Run a small tech startup in two views that share one simulation: an **Executive Dashboard** with financial cards, projections and reports, and a pixel-art **Office** with animated employees.

- Monthly turn-based economy: revenue, salaries, marketing, office costs, churn, reputation.
- Hire and dismiss Developers, Designers, Marketing Specialists and Managers — each with their own salary and productivity.
- Develop and price your product; invest in sprints or major overhauls.
- Four recurring marketing campaigns; monthly financial reports with history and profit chart.
- Expand the office in four levels (4 to 16 desks) and interact with the team, the coffee machine and the whiteboard.
- Win at R$ 1,000,000 net worth — or go bankrupt.
- Play in Portuguese, English or Spanish (French and German in beta). Switch language at any time, mid-game, from Menu → Settings.

## Descrição completa (PT-BR)
Dirija uma startup de tecnologia em duas visões que compartilham a mesma simulação: um **Dashboard Executivo** com indicadores, projeções e relatórios, e um **Escritório** pixel-art com funcionários animados. Economia mensal por turnos, contratação e demissão, desenvolvimento e preço do produto, quatro campanhas de marketing, expansão do escritório em quatro níveis, vitória aos R$ 1.000.000 de patrimônio líquido e falência se o caixa zerar. Disponível em português, inglês e espanhol (francês e alemão em beta); o idioma pode ser trocado a qualquer momento no jogo.

## Instalação (Windows)
1. Baixe `StartupTycoon-windows.zip` e extraia a pasta inteira.
2. Execute `StartupTycoon.exe`. Não é preciso instalar Python.
3. O Windows SmartScreen pode avisar sobre um app desconhecido (o executável não é assinado): "Mais informações → Executar assim mesmo".

## Screenshots
Gerar com `python tools/take_screenshots.py` (pygame real) e enviar os PNG de `docs/screenshots/`. Não há screenshots neste repositório ainda.

## Checklist de envio
- [ ] Gerar o .exe (`tools/build_windows.bat`) e testar em um Windows limpo.
- [ ] Capturar screenshots reais.
- [ ] (opcional) Testar e enviar a versão web (`docs/WEB.md`).
- [ ] Criar o projeto no itch.io com a conta do proprietário; subir o zip com `butler` ou pelo painel.
