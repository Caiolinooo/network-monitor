# Ícones para o Monitor de Rede

Este diretório deve conter os seguintes ícones para a aplicação:

- `favicon.ico` - Ícone da aplicação para o navegador (16x16, 32x32)
- `logo.png` - Logo principal da aplicação (200x50 recomendado)
- `icon-72x72.png` - Ícone PWA 72x72
- `icon-96x96.png` - Ícone PWA 96x96
- `icon-128x128.png` - Ícone PWA 128x128
- `icon-144x144.png` - Ícone PWA 144x144
- `icon-152x152.png` - Ícone PWA 152x152
- `icon-192x192.png` - Ícone PWA 192x192
- `icon-384x384.png` - Ícone PWA 384x384
- `icon-512x512.png` - Ícone PWA 512x512
- `maskable-icon.png` - Ícone adaptável para PWA (512x512 com área segura)
- `badge-72x72.png` - Badge para notificações (72x72)

## Recomendações

- Use um formato PNG com fundo transparente para todos os ícones (exceto favicon.ico)
- Mantenha os ícones consistentes em design, apenas em diferentes tamanhos
- Para o ícone adaptável (maskable-icon.png), certifique-se de que o conteúdo principal esteja dentro da "área segura" (aproximadamente 40% do centro)

## Criação de Ícones

Você pode criar os ícones usando ferramentas como:

- [Inkscape](https://inkscape.org/) (gratuito, código aberto)
- [GIMP](https://www.gimp.org/) (gratuito, código aberto)
- [Adobe Illustrator](https://www.adobe.com/products/illustrator.html) (comercial)
- [Figma](https://www.figma.com/) (gratuito com limitações)

## Conversão para favicon.ico

Para converter um PNG para favicon.ico, você pode usar ferramentas online como:

- [favicon.io](https://favicon.io/)
- [RealFaviconGenerator](https://realfavicongenerator.net/)

Ou usar o ImageMagick via linha de comando:

```bash
convert icon-32x32.png favicon.ico
```