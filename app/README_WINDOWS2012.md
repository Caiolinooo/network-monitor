# Monitor de Rede - Instruções para Windows Server 2012

Este documento contém instruções específicas para executar o Monitor de Rede no Windows Server 2012.

## Novidades

* **Detecção Automática de Sistema**: O script agora detecta automaticamente se está sendo executado no Windows Server 2012 e adapta seu comportamento.
* **Múltiplos Métodos de Inicialização**: Implementados vários métodos de inicialização do servidor que são testados em sequência.
* **Versões Compatíveis de Pacotes**: Instalação automática de versões específicas de pacotes que são compatíveis com Windows Server 2012.

## Requisitos

- Python 3.6.8 (recomendado)
- Acesso de administrador para instalar pacotes

## Instalação passo a passo

### 1. Instalar Python 3.6.8

1. Baixe Python 3.6.8 do site oficial: https://www.python.org/downloads/release/python-368/
2. Escolha a versão Windows x86-64 executable installer
3. Durante a instalação, marque a opção "Add Python to PATH"

### 2. Instalar dependências principais

Execute os comandos abaixo em um PowerShell como administrador:

```powershell
# Atualizar pip para uma versão compatível
python -m pip install --upgrade pip==20.3.4

# Instalar dependências principais
pip install flask==2.0.3
pip install psutil
pip install python-dotenv
pip install flask-cors
pip install pandas==1.1.5
pip install waitress

# Instalar dependências opcionais (versões compatíveis)
pip install Pillow==6.2.2 --only-binary :all:
pip install reportlab==3.5.59 --only-binary :all:
pip install speedtest-cli==2.1.3
```

## Executando o Monitor de Rede

### Método 1: Usando o script principal (Recomendado)

O script principal agora detecta automaticamente o sistema e adapta seu comportamento:

```powershell
cd caminho\para\aplicacao
python app/run.py
```

### Método 2: Usando o script simplificado

Se o método 1 falhar, use o script alternativo específico para Windows Server 2012:

```powershell
cd caminho\para\aplicacao
python app/start_server2012.py
```

### Método 3: Executando os componentes diretamente

Se os métodos anteriores falharem, você pode iniciar o servidor diretamente:

```powershell
cd caminho\para\aplicacao
python app/backend/app.py 5000
```

## Solução de problemas

### 1. Erro "ModuleNotFoundError"

Se você encontrar erros indicando que módulos não foram encontrados, instale-os manualmente:

```powershell
pip install nome-do-modulo
```

### 2. Erro "Porta em uso"

Ambos os scripts agora tentam automaticamente encontrar uma porta alternativa se a padrão estiver em uso.
Você também pode especificar outra porta como argumento:

```powershell
python app/run.py
# ou
python app/start_server2012.py 8080
```

### 3. Erros de compilação

Windows Server 2012 tem limitações para compilar módulos Python. O script agora tenta automaticamente 
instalar versões pré-compiladas dos pacotes problemáticos:

```powershell
pip install nome-do-pacote --only-binary :all:
```

### 4. O aplicativo funciona mas algumas funções não

O Monitor de Rede foi projetado para funcionar mesmo quando algumas dependências opcionais não estão disponíveis:

- Sem ReportLab: relatórios serão gerados como texto simples
- Sem Netifaces: informações limitadas sobre interfaces de rede
- Sem Speedtest: testes de velocidade serão simulados

### 5. Erro "CREATE_NO_WINDOW"

Este erro foi corrigido com a nova abordagem de múltiplos métodos. O script tentará automaticamente
diferentes formas de iniciar o servidor até encontrar uma que funcione.

## Desempenho

Em sistemas antigos como o Windows Server 2012, o Monitor de Rede pode consumir mais recursos. 
Se encontrar problemas de desempenho, considere:

1. Aumentar o intervalo de atualização nas configurações
2. Desativar o monitoramento automático de início
3. Limitar o número de dias de histórico