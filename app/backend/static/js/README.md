# Instruções para o arquivo main.js

## Combinando os arquivos

O arquivo JavaScript principal da aplicação foi dividido em várias partes devido a limitações de tamanho. Para usar a aplicação, combine os arquivos na seguinte ordem:

1. `main.js` (base)
2. `main-part2.js`
3. `main-part3.js`
4. `main-part4.js`
5. `main-part5.js`

## Como combinar

Você pode combinar manualmente copiando e colando o conteúdo de cada arquivo na ordem correta, ou usar um dos métodos abaixo:

### Usando o terminal (Linux/Mac):

```bash
cd app/backend/static/js/
cat main.js main-part2.js main-part3.js main-part4.js main-part5.js > main-combined.js
mv main-combined.js main.js
rm main-part*.js
```

### Usando PowerShell (Windows):

```powershell
cd app\backend\static\js
Get-Content main.js, main-part2.js, main-part3.js, main-part4.js, main-part5.js | Set-Content main-combined.js
Move-Item -Force main-combined.js main.js
Remove-Item main-part*.js
```

## Verificação

Após combinar os arquivos, verifique se o arquivo `main.js` contém todas as funções necessárias:

- `initApp`
- `setupEventListeners`
- `setupCharts`
- `loadSettings`
- `fetchSystemInfo`
- `fetchInterfaces`
- `fetchReports`
- `fetchStatus`
- `startMonitoring`
- `stopMonitoring`
- `resetStats`
- `fetchHistory`
- `startSpeedTest`
- `saveSettings`
- `generateReport`

E todas as funções utilitárias como `formatBytes`, `formatMemory`, etc.

## Observação

Esta divisão foi necessária apenas para o upload inicial. A aplicação espera um único arquivo `main.js` para funcionar corretamente.