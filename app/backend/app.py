"""
Monitor de Rede - Aplicação para monitoramento de desempenho de rede

Autor: Caio Valerio Goulart Correia (Caio Correia)
Email: caiovaleriogoulartcorreia@gmail.com
GitHub: https://github.com/Caiolinooo
LinkedIn: https://www.linkedin.com/in/caio-goulart/
Versão: 1.0.0

Copyright © 2023-2024 Caio Valerio Goulart Correia - Todos os direitos reservados.
Software proprietário licenciado sob termos personalizados.
Uso, distribuição e modificação permitidos apenas mediante autorização expressa do autor.
"""

from flask import Flask, render_template, jsonify, request, send_file, send_from_directory, abort
from flask_cors import CORS
import os
import json
import logging
import sys
import pandas as pd
from datetime import datetime, timedelta
import tempfile
from dotenv import load_dotenv
import time
import platform
import psutil
import socket

# Importações condicionais de bibliotecas que podem falhar
try:
    import speedtest
    SPEEDTEST_AVAILABLE = True
except ImportError:
    SPEEDTEST_AVAILABLE = False
    logging.warning("Biblioteca speedtest-cli não disponível. Testes de velocidade usarão dados simulados.")

try:
    import netifaces
    NETIFACES_AVAILABLE = True
except ImportError:
    NETIFACES_AVAILABLE = False
    logging.warning("Biblioteca netifaces não disponível. Informações de rede serão limitadas.")

try:
    import reportlab
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logging.warning("Biblioteca reportlab não disponível. Exportação de PDF não estará disponível.")

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app_log.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Carregando variáveis de ambiente
load_dotenv()

app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')
CORS(app)

# Diretório para armazenamento de dados
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# Diretório para armazenar relatórios
REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports')
os.makedirs(REPORTS_DIR, exist_ok=True)

# Arquivo para armazenar histórico
HISTORY_FILE = os.path.join(DATA_DIR, 'history.json')

# Arquivo para armazenar configurações
CONFIG_FILE = os.path.join(DATA_DIR, 'config.json')

# Configuração
APP_VERSION = "1.0.0"
MAX_HISTORY_DAYS = 30  # Dias para manter o histórico
MOCK_DATA = True  # Usar dados de exemplo (True) ou coletar dados reais (False)

# Base de dados simulada (para desenvolvimento)
mock_db = {
    "stats": {
        "current_download": 10.5,
        "current_upload": 2.3,
        "current_ping": 25,
        "peak_download": 15.8,
        "peak_upload": 5.2,
        "avg_download": 8.6,
        "avg_upload": 1.9,
        "total_download": 1024 * 1024 * 512,  # 512 MB em bytes
        "total_upload": 1024 * 1024 * 128,    # 128 MB em bytes
    },
    "system_info": {
        "os": f"{platform.system()} {platform.release()}",
        "cpu": platform.processor() or "CPU Info",
        "memory": f"{round(psutil.virtual_memory().total / (1024**3), 2)} GB",
        "uptime": "12:30:45",
        "cpu_percent": 35,
        "memory_percent": 48
    },
    "network_interfaces": [
        {
            "name": "Ethernet",
            "ip": "192.168.1.100",
            "mac": "00:1A:2B:3C:4D:5E",
            "status": "up",
            "type": "Wired"
        },
        {
            "name": "Wi-Fi",
            "ip": "192.168.1.101",
            "mac": "AA:BB:CC:DD:EE:FF",
            "status": "up",
            "type": "Wireless"
        }
    ],
    "history": {
        "daily_data": [
            {
                "date": datetime.now().strftime("%d/%m/%Y"),
                "download": 1024 * 1024 * 512,  # 512 MB em bytes
                "upload": 1024 * 1024 * 128,    # 128 MB em bytes
                "avg_download": 8.6,
                "avg_upload": 1.9,
                "peak_download": 15.8,
                "peak_upload": 5.2
            },
            {
                "date": (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y"),
                "download": 1024 * 1024 * 256,  # 256 MB em bytes
                "upload": 1024 * 1024 * 64,     # 64 MB em bytes
                "avg_download": 7.2,
                "avg_upload": 1.5,
                "peak_download": 12.5,
                "peak_upload": 3.8
            }
        ],
        "three_day_summary": {
            "total_download": 1024 * 1024 * 1024,   # 1 GB em bytes
            "total_upload": 1024 * 1024 * 256,      # 256 MB em bytes
            "avg_download": 7.8,
            "avg_upload": 1.7
        },
        "weekly_summary": {
            "total_download": 1024 * 1024 * 1024 * 3,  # 3 GB em bytes
            "total_upload": 1024 * 1024 * 512,         # 512 MB em bytes
            "avg_download": 8.1,
            "avg_upload": 1.8
        }
    }
}

# Carregar configuração ou criar padrão
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as file:
                return json.load(file)
        except Exception as e:
            logger.error(f"Erro ao carregar configuração: {e}")
    
    # Configuração padrão
    default_config = {
        "update_interval": 5,  # segundos
        "max_history_days": 30,
        "interface": "",  # Auto-detect
        "theme": "light",
        "start_with_monitoring": True,
        "port": 5000
    }
    
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w') as file:
            json.dump(default_config, file, indent=4)
    except Exception as e:
        logger.error(f"Erro ao salvar configuração padrão: {e}")
    
    return default_config

# Carregar as configurações
CONFIG = load_config()

def bytes_to_human_readable(bytes_value):
    """Converte bytes para formato legível (KB, MB, GB)"""
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    i = 0
    while bytes_value >= 1024 and i < len(units) - 1:
        bytes_value /= 1024
        i += 1
    return f"{bytes_value:.2f} {units[i]}"

def get_system_info():
    """Obtém informações do sistema"""
    if MOCK_DATA:
        return mock_db["system_info"]
    
    try:
        uptime = time.time() - psutil.boot_time()
        hours, remainder = divmod(uptime, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return {
            "os": f"{platform.system()} {platform.release()}",
            "cpu": platform.processor() or "CPU Info",
            "memory": f"{round(psutil.virtual_memory().total / (1024**3), 2)} GB",
            "uptime": f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}",
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent
        }
    except Exception as e:
        logger.error(f"Erro ao obter informações do sistema: {e}")
        return {"error": str(e)}

def get_network_interfaces():
    """Obtém lista de interfaces de rede"""
    if MOCK_DATA:
        return mock_db["network_interfaces"]
    
    interfaces = []
    
    try:
        if NETIFACES_AVAILABLE:
            # Usar netifaces se disponível
            for iface in netifaces.interfaces():
                try:
                    addrs = netifaces.ifaddresses(iface)
                    
                    # Para interfaces que têm endereço IPv4
                    if netifaces.AF_INET in addrs:
                        ip = addrs[netifaces.AF_INET][0]['addr']
                        # Se houver endereço MAC disponível
                        mac = ""
                        if netifaces.AF_LINK in addrs:
                            mac = addrs[netifaces.AF_LINK][0]['addr']
                        
                        # Tentar determinar se é interface wireless
                        iface_type = "Unknown"
                        if "wi" in iface.lower() or "wl" in iface.lower():
                            iface_type = "Wireless"
                        elif "eth" in iface.lower() or "en" in iface.lower():
                            iface_type = "Wired"
                        
                        interfaces.append({
                            "name": iface,
                            "ip": ip,
                            "mac": mac,
                            "status": "up",  # Não temos como verificar facilmente
                            "type": iface_type
                        })
                except Exception as e:
                    logger.warning(f"Erro ao processar interface {iface}: {e}")
        else:
            # Fallback para socket se netifaces não estiver disponível
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            
            interfaces.append({
                "name": "Default",
                "ip": ip,
                "mac": "Unknown",
                "status": "up",
                "type": "Unknown"
            })
            
            # No Windows, podemos tentar obter mais informações com ipconfig
            if platform.system() == 'Windows':
                try:
                    import subprocess
                    output = subprocess.check_output('ipconfig /all', shell=True).decode('latin1')
                    
                    # Análise simples do output (não é ideal, mas é um fallback)
                    sections = output.split('\n\n')
                    for section in sections:
                        if 'Adaptador' in section or 'Ethernet adapter' in section:
                            iface_name = section.split(':')[0].strip()
                            
                            # Extrair IP
                            ip_match = None
                            if 'IPv4' in section:
                                for line in section.split('\n'):
                                    if 'IPv4' in line and '.' in line:
                                        ip_match = line.split(':')[-1].strip()
                            
                            # Extrair MAC
                            mac_match = None
                            for line in section.split('\n'):
                                if 'Physical' in line or 'Física' in line:
                                    mac_match = line.split(':')[-1].strip()
                            
                            if ip_match:
                                iface_type = "Wired"
                                if "Wi-Fi" in iface_name or "Wireless" in iface_name:
                                    iface_type = "Wireless"
                                    
                                interfaces.append({
                                    "name": iface_name,
                                    "ip": ip_match,
                                    "mac": mac_match or "Unknown",
                                    "status": "up",
                                    "type": iface_type
                                })
                except Exception as e:
                    logger.warning(f"Fallback para ipconfig falhou: {e}")
    
    except Exception as e:
        logger.error(f"Erro ao obter interfaces de rede: {e}")
    
    return interfaces

def get_network_stats():
    """Obtém estatísticas de rede"""
    if MOCK_DATA:
        return mock_db["stats"]
    
    # Em uma implementação real, você usaria psutil para coletar estatísticas
    # Este é apenas um esboço
    stats = {
        "current_download": 5.5,  # Mbps
        "current_upload": 1.2,    # Mbps
        "current_ping": 30,       # ms
        "peak_download": 10.2,    # Mbps
        "peak_upload": 2.8,       # Mbps
        "avg_download": 4.2,      # Mbps
        "avg_upload": 1.0,        # Mbps
        "total_download": 1024 * 1024 * 256,  # 256 MB em bytes
        "total_upload": 1024 * 1024 * 64,     # 64 MB em bytes
    }
    
    return stats

def get_network_history():
    """Obtém histórico de uso de rede"""
    if MOCK_DATA:
        return mock_db["history"]
    
    # Em uma implementação real, você carregaria os dados do arquivo HISTORY_FILE
    # Este é apenas um esboço
    history = {
        "daily_data": [
            {
                "date": datetime.now().strftime("%d/%m/%Y"),
                "download": 1024 * 1024 * 256,  # 256 MB em bytes
                "upload": 1024 * 1024 * 64,     # 64 MB em bytes
                "avg_download": 4.2,
                "avg_upload": 1.0,
                "peak_download": 10.2,
                "peak_upload": 2.8
            }
        ],
        "three_day_summary": {
            "total_download": 1024 * 1024 * 512,  # 512 MB em bytes
            "total_upload": 1024 * 1024 * 128,    # 128 MB em bytes
            "avg_download": 4.0,
            "avg_upload": 0.9
        },
        "weekly_summary": {
            "total_download": 1024 * 1024 * 1024,  # 1 GB em bytes
            "total_upload": 1024 * 1024 * 256,     # 256 MB em bytes
            "avg_download": 3.8,
            "avg_upload": 0.8
        }
    }
    
    return history

def run_speed_test():
    """Executa um teste de velocidade"""
    if MOCK_DATA:
        # Dados simulados
        time.sleep(2)  # Simular o tempo de teste
        return {
            "download": 95.5,  # Mbps
            "upload": 10.2,    # Mbps
            "ping": 15,        # ms
            "server": "Servidor de teste",
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }
    
    try:
        if SPEEDTEST_AVAILABLE:
            logger.info("Iniciando teste de velocidade real...")
            s = speedtest.Speedtest()
            s.get_best_server()
            
            # Teste de download
            download_speed = s.download() / 1_000_000  # Mbps
            
            # Teste de upload
            upload_speed = s.upload() / 1_000_000  # Mbps
            
            # Obter resultados
            results = s.results.dict()
            
            return {
                "download": round(download_speed, 2),
                "upload": round(upload_speed, 2),
                "ping": round(results["ping"], 2),
                "server": results["server"]["sponsor"],
                "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            }
        else:
            # Dados simulados se speedtest não estiver disponível
            logger.info("Usando teste de velocidade simulado (speedtest não disponível)...")
            return {
                "download": 75.5 + (5 * (random.random() - 0.5)),  # Mbps com variação
                "upload": 8.2 + (2 * (random.random() - 0.5)),    # Mbps com variação
                "ping": 20 + int(10 * random.random()),           # ms com variação
                "server": "Simulação (speedtest-cli não disponível)",
                "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            }
    except Exception as e:
        logger.error(f"Erro no teste de velocidade: {e}")
        return {
            "error": f"Falha no teste de velocidade: {str(e)}",
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }

def generate_report(format="pdf"):
    """Gera um relatório de uso de rede"""
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d%H%M%S")
    
    if format.lower() == "pdf" and REPORTLAB_AVAILABLE:
        # Gerar relatório PDF usando ReportLab
        try:
            filename = f"network_report_{timestamp}.pdf"
            filepath = os.path.join(REPORTS_DIR, filename)
            
            # Obter dados para o relatório
            system_info = get_system_info()
            network_stats = get_network_stats()
            history = get_network_history()
            
            # Criar PDF
            c = canvas.Canvas(filepath, pagesize=letter)
            width, height = letter
            
            # Título
            c.setFont("Helvetica-Bold", 18)
            c.drawString(72, height - 72, "Relatório de Desempenho de Rede")
            
            # Data e hora
            c.setFont("Helvetica", 12)
            c.drawString(72, height - 100, f"Gerado em: {now.strftime('%d/%m/%Y %H:%M:%S')}")
            
            # Informações do sistema
            c.setFont("Helvetica-Bold", 14)
            c.drawString(72, height - 140, "Informações do Sistema")
            
            c.setFont("Helvetica", 12)
            c.drawString(72, height - 160, f"Sistema Operacional: {system_info['os']}")
            c.drawString(72, height - 180, f"CPU: {system_info['cpu']}")
            c.drawString(72, height - 200, f"Memória: {system_info['memory']}")
            c.drawString(72, height - 220, f"Tempo de Atividade: {system_info['uptime']}")
            
            # Estatísticas de rede
            c.setFont("Helvetica-Bold", 14)
            c.drawString(72, height - 260, "Estatísticas de Rede")
            
            c.setFont("Helvetica", 12)
            c.drawString(72, height - 280, f"Download Atual: {network_stats['current_download']} Mbps")
            c.drawString(72, height - 300, f"Upload Atual: {network_stats['current_upload']} Mbps")
            c.drawString(72, height - 320, f"Ping Atual: {network_stats['current_ping']} ms")
            c.drawString(72, height - 340, f"Pico de Download: {network_stats['peak_download']} Mbps")
            c.drawString(72, height - 360, f"Pico de Upload: {network_stats['peak_upload']} Mbps")
            
            # Total de dados
            c.setFont("Helvetica-Bold", 14)
            c.drawString(72, height - 400, "Total de Dados")
            
            c.setFont("Helvetica", 12)
            c.drawString(72, height - 420, f"Total Download: {bytes_to_human_readable(network_stats['total_download'])}")
            c.drawString(72, height - 440, f"Total Upload: {bytes_to_human_readable(network_stats['total_upload'])}")
            
            # Resumo semanal
            c.setFont("Helvetica-Bold", 14)
            c.drawString(72, height - 480, "Resumo Semanal")
            
            c.setFont("Helvetica", 12)
            c.drawString(72, height - 500, f"Download Total: {bytes_to_human_readable(history['weekly_summary']['total_download'])}")
            c.drawString(72, height - 520, f"Upload Total: {bytes_to_human_readable(history['weekly_summary']['total_upload'])}")
            c.drawString(72, height - 540, f"Média de Download: {history['weekly_summary']['avg_download']} Mbps")
            c.drawString(72, height - 560, f"Média de Upload: {history['weekly_summary']['avg_upload']} Mbps")
            
            # Finalizar o PDF
            c.showPage()
            c.save()
            
            logger.info(f"Relatório PDF gerado: {filepath}")
            return {"filename": filename, "path": filepath, "format": "pdf"}
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório PDF: {e}")
            # Fallback para texto se o PDF falhar
            return generate_report(format="txt")
    else:
        # Gerar relatório de texto (fallback)
        try:
            filename = f"network_report_{timestamp}.txt"
            filepath = os.path.join(REPORTS_DIR, filename)
            
            # Obter dados para o relatório
            system_info = get_system_info()
            network_stats = get_network_stats()
            history = get_network_history()
            
            with open(filepath, 'w') as f:
                f.write("====================================================\n")
                f.write("           RELATÓRIO DE DESEMPENHO DE REDE          \n")
                f.write("====================================================\n\n")
                
                f.write(f"Gerado em: {now.strftime('%d/%m/%Y %H:%M:%S')}\n\n")
                
                f.write("INFORMAÇÕES DO SISTEMA\n")
                f.write("-----------------------\n")
                f.write(f"Sistema Operacional: {system_info['os']}\n")
                f.write(f"CPU: {system_info['cpu']}\n")
                f.write(f"Memória: {system_info['memory']}\n")
                f.write(f"Tempo de Atividade: {system_info['uptime']}\n\n")
                
                f.write("ESTATÍSTICAS DE REDE\n")
                f.write("--------------------\n")
                f.write(f"Download Atual: {network_stats['current_download']} Mbps\n")
                f.write(f"Upload Atual: {network_stats['current_upload']} Mbps\n")
                f.write(f"Ping Atual: {network_stats['current_ping']} ms\n")
                f.write(f"Pico de Download: {network_stats['peak_download']} Mbps\n")
                f.write(f"Pico de Upload: {network_stats['peak_upload']} Mbps\n\n")
                
                f.write("TOTAL DE DADOS\n")
                f.write("--------------\n")
                f.write(f"Total Download: {bytes_to_human_readable(network_stats['total_download'])}\n")
                f.write(f"Total Upload: {bytes_to_human_readable(network_stats['total_upload'])}\n\n")
                
                f.write("RESUMO SEMANAL\n")
                f.write("--------------\n")
                f.write(f"Download Total: {bytes_to_human_readable(history['weekly_summary']['total_download'])}\n")
                f.write(f"Upload Total: {bytes_to_human_readable(history['weekly_summary']['total_upload'])}\n")
                f.write(f"Média de Download: {history['weekly_summary']['avg_download']} Mbps\n")
                f.write(f"Média de Upload: {history['weekly_summary']['avg_upload']} Mbps\n\n")
                
                f.write("====================================================\n")
                f.write("  Monitor de Rede v" + APP_VERSION + " - © 2023-2024 Caio Correia  \n")
                f.write("====================================================\n")
            
            logger.info(f"Relatório de texto gerado: {filepath}")
            return {"filename": filename, "path": filepath, "format": "txt"}
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório de texto: {e}")
            return {"error": str(e)}

# Rotas da API
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/system-info')
def api_system_info():
    """API para obter informações do sistema"""
    return jsonify(get_system_info())

@app.route('/api/network-interfaces')
def api_network_interfaces():
    """API para listar interfaces de rede"""
    return jsonify(get_network_interfaces())

@app.route('/api/stats')
def api_stats():
    """API para obter estatísticas de rede"""
    return jsonify(get_network_stats())

@app.route('/api/history')
def api_history():
    """API para obter histórico de uso de rede"""
    return jsonify(get_network_history())

@app.route('/api/speed-test', methods=['POST'])
def api_speed_test():
    """API para executar teste de velocidade"""
    return jsonify(run_speed_test())

@app.route('/api/export-report', methods=['POST'])
def api_export_report():
    """API para exportar relatório"""
    format = request.json.get('format', 'pdf').lower()
    if format not in ['pdf', 'txt']:
        return jsonify({"error": "Formato inválido. Use 'pdf' ou 'txt'."})
    
    report = generate_report(format)
    return jsonify(report)

@app.route('/api/download-report/<filename>')
def api_download_report(filename):
    """API para baixar um relatório gerado"""
    try:
        return send_from_directory(REPORTS_DIR, filename, as_attachment=True)
    except Exception as e:
        logger.error(f"Erro ao baixar relatório: {e}")
        return jsonify({"error": f"Arquivo não encontrado: {filename}"}), 404

@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    """API para obter/atualizar configurações"""
    global CONFIG
    
    # POST para atualizar configurações
    if request.method == 'POST':
        try:
            new_config = request.json
            
            # Validar e mesclar configurações
            if "update_interval" in new_config:
                CONFIG["update_interval"] = max(1, int(new_config["update_interval"]))
            
            if "max_history_days" in new_config:
                CONFIG["max_history_days"] = max(1, min(365, int(new_config["max_history_days"])))
            
            if "interface" in new_config:
                CONFIG["interface"] = new_config["interface"]
            
            if "theme" in new_config:
                CONFIG["theme"] = new_config["theme"]
            
            if "start_with_monitoring" in new_config:
                CONFIG["start_with_monitoring"] = bool(new_config["start_with_monitoring"])
            
            # Salvar configurações
            with open(CONFIG_FILE, 'w') as file:
                json.dump(CONFIG, file, indent=4)
            
            return jsonify({"success": True, "config": CONFIG})
        except Exception as e:
            logger.error(f"Erro ao atualizar configurações: {e}")
            return jsonify({"success": False, "message": str(e)})
    
    # GET
    return jsonify(CONFIG)

@app.route('/api/status')
def api_status():
    """API para verificar status da aplicação"""
    return jsonify({
        "status": "online",
        "version": APP_VERSION,
        "timestamp": int(time.time()),
        "uptime": get_system_info()["uptime"]
    })

# Servir arquivos estáticos para o PWA
@app.route('/static/icons/<path:filename>')
def serve_icon(filename):
    icons_dir = os.path.join(app.static_folder, 'icons')
    return send_from_directory(icons_dir, filename)

# Tratamento de erros
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Recurso não encontrado"}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Erro interno do servidor"}), 500

if __name__ == '__main__':
    # Verificar se a porta foi fornecida como argumento de linha de comando
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            logger.error(f"Porta inválida: {sys.argv[1]}. Usando porta padrão.")
            port = int(os.environ.get('PORT', 5000))
    else:
        port = int(os.environ.get('PORT', 5000))
    
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # Criar diretório de dados se não existir
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    logger.info(f"Iniciando Monitor de Rede v{APP_VERSION} na porta {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)