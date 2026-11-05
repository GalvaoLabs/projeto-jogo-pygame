# Versão web (Pygbag / WebAssembly) — análise de viabilidade

**Status: PARCIALMENTE IMPLEMENTADA, NÃO TESTADA EM NAVEGADOR.** Nada aqui foi executado em um
navegador real; o ambiente onde o código foi preparado não tinha acesso ao PyPI (não foi possível
instalar `pygbag` nem `pygame`). Não publique como "HTML5" no itch.io antes de fazer o checklist abaixo.

## O que já foi adaptado no código (e não afeta o desktop)
| Requisito do Pygbag | Situação |
| --- | --- |
| Loop assíncrono (`await asyncio.sleep(0)` por quadro) | `Game.run_async()` + `main.py` com `asyncio.run(main())`. No desktop usa o mesmo loop. |
| Sem `pygame.font.SysFont` (não há fontes do sistema no navegador) | O jogo usa DejaVu embutida em `assets/fonts/` (SysFont só como último recurso). |
| Sem sons, sem numpy, sem arquivos externos | O jogo desenha tudo com primitivas; só carrega JSON e 2 TTF. |
| Caminhos de recursos | `systems/paths.py` resolve relativo ao código (funciona no sistema de arquivos virtual). |
| Botão "Sair" e "Tela cheia" não fazem sentido numa aba | Ocultos quando `sys.platform == "emscripten"`. |
| Gravação de configurações | `settings.json` vai para `/data/data/startup_tycoon` e falha de escrita **nunca** derruba o jogo. |

## Avaliação
- **Tecnicamente plausível**: Pygame 2 com primitivas 2D, ~1280×720, sem áudio e sem bibliotecas nativas é o caso
  mais simples para o Pygbag. O custo de CPU por quadro é baixo (apenas retângulos e texto).
- **Riscos reais (precisam de teste)**:
  1. *Desempenho do texto*: o jogo renderiza texto a cada quadro (sem cache). Em WebAssembly isso pode ser mais lento
     que no desktop. Se o FPS cair, o primeiro ajuste é cachear `font.render` por `(texto, tamanho, cor)`.
  2. *Persistência*: o sistema de arquivos do Pygbag é em memória; o idioma só sobrevive entre visitas se o diretório
     persistente for sincronizado com o IndexedDB. Não verificado — se falhar, o jogo volta para pt_BR a cada visita.
  3. *`pygame.SCALED`* é usado só em tela cheia (oculta na web).
  4. Primeiro carregamento baixa o runtime do Pygbag (CDN) — exige internet.

## Como gerar e testar
```
pip install -r requirements-dev.txt
bash tools/build_web.sh                  # empacota só os arquivos de runtime em build/web_src
python -m pygbag build/web_src           # servidor local em http://localhost:8000
```
### Checklist antes de declarar "pronta"
- [ ] Abre no Chrome e no Firefox sem erro no console.
- [ ] Menu → Novo Jogo → todas as abas → Encerrar mês → vitória/falência funcionam.
- [ ] Trocar idioma durante a partida atualiza as telas; acentos (ç, ã, ñ, ß, é, €) aparecem corretos.
- [ ] FPS aceitável (≥ 30) no Dashboard e no Escritório (16 mesas).
- [ ] Idioma escolhido persiste ao recarregar a página (ou documentar que não persiste).
- [ ] Mouse/cliques corretos com a página redimensionada.
