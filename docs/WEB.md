# Versão web (Pygbag / WebAssembly)

**Build pronto para itch.io; partida no navegador ainda não confirmada.** O ZIP foi gerado e verificado: contém `index.html` na raiz, `favicon.png` e `web_src.apk`. O runtime Pygbag exige um clique/toque inicial.

## Gerar o pacote

Na raiz do projeto:

```powershell
python -m pip install -r requirements.txt
python tools/build_web.py
```

O arquivo para upload é `build/startup-tycoon-itch.zip`. O script cria também `build/web/`, que pode ser servido localmente para inspeção. Ele usa Pygbag 0.9.3 e baixa o runtime do CDN do Pygbag; o navegador precisa de internet no primeiro carregamento.

O script remove a tag BrowserFS gerada pelo template porque o arquivo do CDN retorna 404; o jogo não usa BrowserFS para executar. As configurações web continuam sujeitas ao sistema de arquivos em memória do navegador.

## Publicar no itch.io

1. Crie ou edite uma página no itch.io e escolha **HTML Game**.
2. Envie `build/startup-tycoon-itch.zip`.
3. Use a opção de jogar embutido na página e configure o quadro em 1280 × 720. Deixe **Click to play** ligado.
4. Faça uma prévia no itch.io. Na primeira tela, clique no jogo para iniciar.

O ZIP segue o formato HTML5 do itch.io: `index.html` está no nível principal e o arquivo inclui os recursos de runtime necessários. Veja as [regras oficiais de jogos HTML5 do itch.io](https://itch.io/docs/creators/html5).

## GitHub Actions

O workflow `.github/workflows/deploy-web.yml` gera o pacote em cada mudança relevante na `main` e guarda um artefato chamado `startup-tycoon-itch-html5` por 30 dias. Ele também prepara o artefato para GitHub Pages; para publicar Pages, a fonte do Pages precisa estar configurada como GitHub Actions nas configurações do repositório.

## Limite de validação

A estrutura do ZIP e o build Pygbag foram verificados localmente. Não consegui confirmar o início e a jogabilidade no navegador controlado, então não declarei o jogo pronto para jogadores. Antes de divulgar a página do itch.io, confira o menu, Novo Jogo, troca Dashboard/Escritório e Encerrar mês.
