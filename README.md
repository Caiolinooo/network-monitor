# Monitor de Rede

Aplicação web para monitoramento de desempenho de rede com suporte para PWA (Progressive Web App) e exportação de relatórios.

## Características

- Monitoramento em tempo real de download, upload e latência
- Histórico de uso de dados com gráficos detalhados
- Testes de velocidade integrados
- Exportação de relatórios em PDF
- Compatível com PWA para uso offline
- Detecção automática de interfaces de rede
- Suporte para tema claro/escuro
- Compatível com Windows, Linux e macOS
- Suporte especial para Windows Server 2012

## Instalação

### Método Rápido

1. Clone o repositório ou baixe os arquivos
2. Execute o script de inicialização:

```bash
python app/run.py
```

### Instalação Manual de Dependências

Se preferir instalar as dependências manualmente:

```bash
pip install flask psutil python-dotenv flask-cors pandas Pillow
pip install reportlab speedtest-cli netifaces
```

Para Windows Server 2012, consulte o arquivo `README_WINDOWS2012.md` para instruções específicas.

## Uso

### Iniciando o Monitor

Após executar o script, o servidor será iniciado em `http://localhost:5000` e o navegador será aberto automaticamente.

Você também pode acessar o aplicativo de qualquer dispositivo na mesma rede através do endereço IP do servidor.

### Navegação

- **Painel Principal**: Visualize estatísticas em tempo real
- **Histórico**: Analise o uso de dados ao longo do tempo
- **Teste de Velocidade**: Execute testes de velocidade sob demanda
- **Configurações**: Personalize as configurações do aplicativo
- **Relatórios**: Gere e exporte relatórios

### Iniciar/Parar Monitoramento

O monitoramento pode ser iniciado ou interrompido a qualquer momento através do botão no painel principal.

### Usando como PWA

Ao acessar a aplicação em um navegador compatível, você verá a opção de "Instalar" ou "Adicionar à tela inicial". Isso permitirá que você use o Monitor de Rede como um aplicativo nativo, mesmo offline.

## Personalização

O arquivo de configuração está localizado em `app/backend/data/config.json` e contém as seguintes opções:

```json
{
  "port": 5000,
  "theme": "light",
  "start_with_monitoring": true,
  "update_interval": 5,
  "interface": "",
  "max_history_days": 30
}
```

Você pode modificar estas configurações diretamente pelo arquivo ou através da interface de usuário na seção de Configurações.

## Inicialização Automática

### Windows

Para configurar o Monitor de Rede para iniciar automaticamente com o Windows:

1. Crie um atalho para `run.py`
2. Pressione `Win+R`, digite `shell:startup` e pressione Enter
3. Mova o atalho para a pasta que se abriu

### Linux/macOS

Adicione o seguinte ao seu crontab:

```
@reboot python /caminho/para/app/run.py
```

## Licença

Licença de Software Proprietário

**Restrições:**
- Uso comercial: Proibido sem autorização
- Uso privado: Permitido
- Validade: 1 ano
- Distribuição: Proibida sem autorização
- Modificação: Proibida sem autorização
- Lei aplicável: Leis do Brasil

O software é fornecido "no estado em que se encontra", sem garantias de qualquer tipo.

© 2023-2025 Caio Valerio Goulart Correia. Todos os direitos reservados.
