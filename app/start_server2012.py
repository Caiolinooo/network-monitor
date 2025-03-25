#!/usr/bin/env python3
"""
Monitor de Rede - Script de inicialização simplificado para Windows Server 2012
Versão simplificada sem verificação de dependências opcionais
"""

import os
import sys
import subprocess
import time
import socket
import logging
import platform

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='monitor_app.log',
    filemode='a'
)
logger = logging.getLogger("monitor-app")

# Porta padrão
DEFAULT_PORT = 5000

def get_local_ip():
    """Obtém o endereço IP local para acesso pela rede"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'

def is_port_available(port):
    """Verifica se a porta está disponível"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', port))
        return True
    except:
        return False

def start_server():
    """Inicia o servidor Flask da forma mais simples possível"""
    # Verificar argumentos de linha de comando para a porta
    port = DEFAULT_PORT
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
            print(f"Usando porta especificada: {port}")
        except ValueError:
            print(f"Porta inválida: {sys.argv[1]}. Usando porta padrão {DEFAULT_PORT}.")
    
    # Verificar porta disponível
    if not is_port_available(port):
        print(f"Porta {port} não está disponível.")
        for alternative_port in range(port + 1, port + 20):
            if is_port_available(alternative_port):
                port = alternative_port
                print(f"Usando porta alternativa: {port}")
                break
        else:
            print("Erro: Nenhuma porta disponível.")
            return
    
    # Caminho para o arquivo app.py
    backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend', 'app.py')
    
    if not os.path.exists(backend_path):
        print(f"Erro: Arquivo do backend não encontrado: {backend_path}")
        return
    
    # Detectar sistema operacional
    print(f"Sistema operacional: {platform.system()} {platform.release()} ({platform.version()})")
    
    try:
        print(f"Iniciando servidor na porta {port}...")
        
        # Tentar métodos diferentes baseados no sistema operacional
        if platform.system() == 'Windows':
            # Tentar diferentes métodos para o Windows, em ordem de preferência
            methods = [
                # Método 1: Usando startupinfo (mais compatível com 2012)
                lambda: subprocess.Popen(
                    [sys.executable, backend_path, str(port)],
                    startupinfo=get_startup_info(),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                ),
                # Método 2: Usando shell=True
                lambda: subprocess.Popen(
                    f'"{sys.executable}" "{backend_path}" {port}',
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                ),
                # Método 3: Diretamente sem configuração especial
                lambda: subprocess.Popen(
                    [sys.executable, backend_path, str(port)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            ]
            
            # Tente cada método até um funcionar
            process = None
            last_error = None
            for i, method in enumerate(methods):
                try:
                    process = method()
                    break
                except Exception as e:
                    last_error = e
                    print(f"Método {i+1} falhou: {e}")
                    continue
            
            if process is None:
                raise Exception(f"Todos os métodos falharam. Último erro: {last_error}")
        else:
            # Para Linux/Mac
            process = subprocess.Popen(
                [sys.executable, backend_path, str(port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        
        time.sleep(2)  # Espera o servidor iniciar
        
        if process.poll() is not None:
            # O processo terminou prematuramente
            out, err = process.communicate()
            err_msg = err.decode('utf-8', errors='replace')
            print(f"Erro ao iniciar o servidor: {err_msg}")
            return
        
        ip = get_local_ip()
        print("\nServidor iniciado com sucesso!")
        print(f"Acesse o aplicativo em:")
        print(f"  - Local: http://127.0.0.1:{port}")
        print(f"  - Rede: http://{ip}:{port}")
        print("\nPressione Ctrl+C para encerrar o servidor quando terminar\n")
        
        # Mantém o script em execução para que o usuário possa ver as mensagens
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\nEncerrando servidor...")
            process.terminate()
            process.wait(timeout=5)
            print("Servidor encerrado.")
    
    except Exception as e:
        print(f"Erro ao iniciar o servidor: {e}")

def get_startup_info():
    """Cria objeto STARTUPINFO para ocultar janela no Windows"""
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = 0  # SW_HIDE
    return startupinfo

if __name__ == '__main__':
    print("\n=== Monitor de Rede - Inicialização Simplificada para Windows Server 2012 ===\n")
    start_server()