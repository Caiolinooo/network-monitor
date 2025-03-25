#!/usr/bin/env python3
"""
Monitor de Rede - Script de inicialização
Verifica dependências, configura ambiente e inicia a aplicação
"""

import os
import sys
import subprocess
import time
import webbrowser
import platform
import socket
import logging
import json
from pathlib import Path
from datetime import datetime
import importlib

# Configuração de logging
log_file = 'monitor_app.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("monitor-app")

# Versão mínima do Python requerida
REQUIRED_PYTHON_VERSION = (3, 6)

# Lista de dependências requeridas e opcionais
REQUIRED_PACKAGES = [
    'flask',
    'psutil',
    'python-dotenv',
    'flask-cors',
    'Pillow',
    'pandas'
]

# Dependências que podem falhar em alguns sistemas
OPTIONAL_PACKAGES = [
    'reportlab',  # Para geração de PDF, pode requerer compilação
    'speedtest-cli',  # Para testes de velocidade
    'netifaces'   # Para detalhes de rede, pode requerer compilação
]

# Configurações
APP_VERSION = "1.0.0"
DEFAULT_PORT = 5000
CONFIG_DIR = Path(os.path.dirname(os.path.abspath(__file__)), 'backend', 'data')
CONFIG_FILE = CONFIG_DIR / 'config.json'

def print_banner():
    """Exibe um banner com informações da aplicação"""
    banner = r"""
 __  __             _ _             _        _____        _      
|  \/  |           (_) |           | |      |  __ \      | |     
| \  / | ___  _ __  _| |_ ___  _ __| |______| |__) |___  | | ___ 
| |\/| |/ _ \| '_ \| | __/ _ \| '__| |______|  _  // _ \ | |/ _ \
| |  | | (_) | | | | | || (_) | |  | |      | | \ \  __/ | |  __/
|_|  |_|\___/|_| |_|_|\__\___/|_|  |_|      |_|  \_\___| |_|\___|                                                             
                                                                 
Monitor de Rede v{} - Inicializando...
    """.format(APP_VERSION)
    
    print(banner)
    logger.info(f"Monitor de Rede v{APP_VERSION} inicializando")

def check_python_version():
    """Verifica se a versão do Python atende aos requisitos mínimos"""
    current_python = sys.version_info
    
    logger.info(f"Verificando versão do Python: {platform.python_version()}")
    
    if current_python.major < REQUIRED_PYTHON_VERSION[0] or \
       (current_python.major == REQUIRED_PYTHON_VERSION[0] and 
        current_python.minor < REQUIRED_PYTHON_VERSION[1]):
        logger.error(
            f"Versão do Python incompatível. Requer Python {REQUIRED_PYTHON_VERSION[0]}.{REQUIRED_PYTHON_VERSION[1]} ou superior. "
            f"Versão atual: {current_python.major}.{current_python.minor}"
        )
        print(f"Erro: Este aplicativo requer Python {REQUIRED_PYTHON_VERSION[0]}.{REQUIRED_PYTHON_VERSION[1]} ou superior.")
        print(f"Você está usando Python {current_python.major}.{current_python.minor}")
        sys.exit(1)
    
    logger.info("Verificação da versão do Python concluída com sucesso")
    return True

def detect_system():
    """Detecta o sistema operacional e versão para adaptação de compatibilidade"""
    os_name = platform.system()
    os_version = platform.version()
    os_release = platform.release()
    
    system_info = {
        "name": os_name,
        "version": os_version,
        "release": os_release,
        "is_windows": os_name == "Windows",
        "is_linux": os_name == "Linux",
        "is_mac": os_name == "Darwin",
        "is_windows_server_2012": os_name == "Windows" and ("2012" in os_version or "6.2" in os_version),
        "is_windows_7_or_older": os_name == "Windows" and ("6.1" in os_version or "6.0" in os_version or "5." in os_version),
        "detail": f"{os_name} {os_release} ({os_version})"
    }
    
    logger.info(f"Sistema detectado: {system_info['detail']}")
    return system_info

SYSTEM_INFO = detect_system()

def check_dependencies():
    """Verifica se as dependências necessárias estão instaladas."""
    logging.info("Verificando dependências...")
    missing_packages = []
    warn_packages = []
    
    # Verificar pacotes requeridos
    for package in REQUIRED_PACKAGES:
        try:
            importlib.import_module(package.replace('-', '_'))
            logging.info(f"Pacote {package} encontrado")
        except ImportError:
            missing_packages.append(package)
            logging.warning(f"Pacote {package} não encontrado")
    
    # Verificar pacotes opcionais
    for package in OPTIONAL_PACKAGES:
        try:
            importlib.import_module(package.replace('-', '_'))
            logging.info(f"Pacote {package} encontrado")
        except ImportError:
            warn_packages.append(package)
            logging.warning(f"Pacote {package} não encontrado")
    
    # Se houver pacotes faltando, perguntar se deseja instalar
    if missing_packages or warn_packages:
        print("\nAs seguintes dependências estão faltando:")
        for pkg in missing_packages:
            print(f"  - {pkg}")
        for pkg in warn_packages:
            print(f"  - {pkg} (opcional)")
        
        if missing_packages:  # Só pergunta se faltarem pacotes obrigatórios
            try:
                resp = input("Deseja instalar as dependências faltantes? (s/n): ")
                if resp.lower() == 's':
                    logging.info("Instalando dependências...")
                    
                    # Instala pacotes obrigatórios
                    if missing_packages:
                        try:
                            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
                        except subprocess.CalledProcessError:
                            logging.error("Falha ao instalar pacotes obrigatórios")
                            print("Erro: Falha ao instalar alguns pacotes obrigatórios.")
                            return False
                    
                    # Instala pacotes opcionais adaptados ao sistema
                    if warn_packages:
                        for package in warn_packages:
                            try:
                                if SYSTEM_INFO['is_windows_server_2012'] and package in ['reportlab', 'Pillow', 'netifaces']:
                                    # Usar versões específicas e apenas binários no Windows Server 2012
                                    if package == 'reportlab':
                                        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'reportlab==3.5.59', '--only-binary', ':all:'])
                                    elif package == 'Pillow':
                                        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'Pillow==6.2.2', '--only-binary', ':all:'])
                                    elif package == 'netifaces':
                                        # Pular netifaces em Server 2012, é complicado de instalar
                                        logging.warning("Pulando netifaces em Windows Server 2012 - biblioteca opcional")
                                    else:
                                        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                                else:
                                    # Instalação normal para outros sistemas
                                    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                            except:
                                logging.warning(f"Não foi possível instalar o pacote opcional {package}")
                    
                    print("Dependências instaladas com sucesso!")
                    logging.info("Dependências instaladas com sucesso")
            except:
                pass
    
    logging.info("Todas as dependências estão instaladas")
    return True

def get_local_ip():
    """Obtém o endereço IP local para acesso pela rede"""
    try:
        # Cria um socket UDP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Não precisamos realmente se conectar a este endereço, apenas fingir
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
        s.close()
        logger.info(f"Endereço IP local: {ip}")
        return ip
    except Exception as e:
        logger.error(f"Erro ao obter endereço IP local: {e}")
        return '127.0.0.1'

def is_port_available(port):
    """Verifica se a porta está disponível para uso"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', port))
        logger.info(f"Porta {port} está disponível")
        return True
    except OSError:
        logger.warning(f"Porta {port} não está disponível")
        return False

def load_config():
    """Carrega ou cria o arquivo de configuração"""
    try:
        if not CONFIG_DIR.exists():
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            logger.info(f"Diretório de configuração criado: {CONFIG_DIR}")
        
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                logger.info("Configuração carregada com sucesso")
                return config
        
        # Configuração padrão
        config = {
            "port": DEFAULT_PORT,
            "theme": "light",
            "start_with_monitoring": True,
            "update_interval": 5,
            "interface": "",
            "max_history_days": 30
        }
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
            logger.info("Configuração padrão criada")
        
        return config
    except Exception as e:
        logger.error(f"Erro ao carregar configuração: {e}")
        return {"port": DEFAULT_PORT}

def start_backend(port):
    """Inicia o servidor backend Flask adaptando-se ao sistema operacional"""
    try:
        logger.info(f"Iniciando servidor no {SYSTEM_INFO['detail']} na porta {port}")
        backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend', 'app.py')
        
        # Verificar se o arquivo existe
        if not os.path.exists(backend_path):
            logger.error(f"Arquivo do backend não encontrado: {backend_path}")
            print(f"Erro: Arquivo do backend não encontrado: {backend_path}")
            return False
            
        # Diferentes métodos de inicialização baseados no sistema operacional
        if SYSTEM_INFO['is_windows']:
            # Windows Server 2012 ou sistemas Windows mais antigos precisam de tratamento especial
            if SYSTEM_INFO['is_windows_server_2012'] or SYSTEM_INFO['is_windows_7_or_older']:
                logger.info("Usando método de inicialização compatível com Windows Server 2012")
                try:
                    # Método 1: Usando STARTUPINFO para ocultar a janela
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = 0  # SW_HIDE
                    
                    process = subprocess.Popen(
                        [sys.executable, backend_path, str(port)],
                        startupinfo=startupinfo,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                except Exception as e1:
                    logger.warning(f"Método 1 falhou: {e1}. Tentando método alternativo...")
                    try:
                        # Método 2: Usando shell=True como fallback
                        process = subprocess.Popen(
                            f'"{sys.executable}" "{backend_path}" {port}',
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                        )
                    except Exception as e2:
                        logger.error(f"Método 2 também falhou: {e2}")
                        raise
            else:
                # Windows moderno - pode usar CREATE_NO_WINDOW
                logger.info("Usando método de inicialização para Windows moderno")
                try:
                    process = subprocess.Popen(
                        [sys.executable, backend_path, str(port)],
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                except AttributeError:
                    # Se CREATE_NO_WINDOW não existir, usar método alternativo
                    logger.warning("CREATE_NO_WINDOW não disponível, usando método alternativo")
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = 0
                    process = subprocess.Popen(
                        [sys.executable, backend_path, str(port)],
                        startupinfo=startupinfo,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
        else:
            # Linux/Mac
            logger.info("Usando método de inicialização para Unix/Linux/Mac")
            process = subprocess.Popen(
                [sys.executable, backend_path, str(port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        
        # Aguarda um momento para o servidor iniciar
        time.sleep(2)
        
        # Verifica se o processo ainda está em execução
        if process.poll() is not None:
            # O processo terminou prematuramente
            out, err = process.communicate()
            err_msg = err.decode('utf-8', errors='replace')
            logger.error(f"Servidor encerrou prematuramente: {err_msg}")
            print(f"Erro ao iniciar o servidor: {err_msg}")
            return False
        
        # Armazena o PID para possível uso posterior
        with open('server.pid', 'w') as f:
            f.write(str(process.pid))
        
        logger.info(f"Servidor iniciado com PID {process.pid}")
        print(f"Servidor iniciado na porta {port}")
        
        ip = get_local_ip()
        print(f"Acesse o aplicativo em:")
        print(f"  - Local: http://127.0.0.1:{port}")
        print(f"  - Rede: http://{ip}:{port}")
        
        return port
    except Exception as e:
        logger.error(f"Erro ao iniciar o servidor: {e}")
        print(f"Erro ao iniciar o servidor: {e}")
        
        # Se falhar usando o método padrão e estivermos no Windows, sugerir usar o script simplificado
        if SYSTEM_INFO['is_windows']:
            alt_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'start_server2012.py')
            if os.path.exists(alt_script):
                print("\nSugestão: Tente usar o script simplificado para Windows Server:")
                print(f"python {alt_script}")
        
        return False

def open_browser(port):
    """Abre o navegador com a aplicação"""
    try:
        url = f"http://127.0.0.1:{port}"
        logger.info(f"Abrindo navegador em {url}")
        
        # Aguarda um pouco mais para garantir que o servidor esteja pronto
        time.sleep(1)
        
        # Tenta abrir o navegador padrão
        webbrowser.open(url)
        logger.info("Navegador aberto com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro ao abrir navegador: {e}")
        print(f"Nota: Não foi possível abrir o navegador automaticamente. Acesse http://127.0.0.1:{port}")
        return False

def main():
    """Função principal que coordena a inicialização da aplicação"""
    print_banner()
    
    # Verificar requisitos do sistema
    if not check_python_version():
        return 1
    
    if not check_dependencies():
        return 1
    
    # Carregar configuração
    config = load_config()
    port = config.get("port", DEFAULT_PORT)
    
    # Verificar disponibilidade da porta
    if not is_port_available(port):
        for alternative_port in range(port + 1, port + 10):
            if is_port_available(alternative_port):
                logger.warning(f"Porta {port} não disponível. Usando porta {alternative_port}")
                print(f"Aviso: Porta {port} não disponível. Usando porta {alternative_port}")
                port = alternative_port
                break
        else:
            logger.error("Nenhuma porta disponível")
            print("Erro: Não foi possível encontrar uma porta disponível.")
            return 1
    
    # Iniciar o backend
    result = start_backend(port)
    if not result:
        return 1
    
    # Abrir o navegador
    open_browser(port)
    
    print("\nO Monitor de Rede está em execução.")
    print("Pressione Ctrl+C neste terminal para encerrar a aplicação.")
    
    try:
        # Manter script em execução
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Aplicação encerrada pelo usuário")
        print("\nMonitor de Rede encerrado.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())