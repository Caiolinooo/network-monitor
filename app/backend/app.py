"""
Monitor de Rede - Aplicação para monitoramento de desempenho de rede
Autor: Caio Valerio Goulart Correia
Email: caio.correia@exemplo.com
GitHub: https://github.com/Caiolinooo
LinkedIn: https://linkedin.com/in/caiovalerio
Versão: 1.0.0
Copyright © 2023-2024 Todos os direitos reservados.
Software proprietário licenciado sob termos personalizados.
Uso, distribuição e modificação permitidos apenas com permissão expressa do autor.
"""

import os
import sys
import time
import json
import logging
import socket
import platform
import datetime
import random
from pathlib import Path
from threading import Thread, Lock
from logging.handlers import RotatingFileHandler

from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS

# Importações condicionais para lidar com dependências opcionais
SPEEDTEST_AVAILABLE = True
try:
    import speedtest
except ImportError:
    SPEEDTEST_AVAILABLE = False
    logging.warning("Módulo 'speedtest-cli' não encontrado. Testes de velocidade simulados serão usados.")

NETIFACES_AVAILABLE = True
try:
    import netifaces
except ImportError:
    NETIFACES_AVAILABLE = False
    logging.warning("Módulo 'netifaces' não encontrado. Detecção de interfaces limitada será usada.")

REPORTLAB_AVAILABLE = True
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
except ImportError:
    REPORTLAB_AVAILABLE = False
    logging.warning("Módulo 'reportlab' não encontrado. Relatórios PDF não estarão disponíveis.")

# Configuração de logging
def setup_logging(log_dir=None):
    if not log_dir:
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'network_monitor.log')
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Handler para arquivo com rotação
    file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(console_handler)
    
    return logger

# Inicializa o logger
logger = setup_logging()

# Caminhos importantes
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
STATIC_DIR = os.path.join(BASE_DIR, 'static')
REPORTS_DIR = os.path.join(DATA_DIR, 'reports')
HISTORY_FILE = os.path.join(DATA_DIR, 'history.json')
CONFIG_FILE = os.path.join(DATA_DIR, 'config.json')

# Cria diretórios necessários
for directory in [DATA_DIR, REPORTS_DIR]:
    os.makedirs(directory, exist_ok=True)

# Inicializa a aplicação Flask
app = Flask(__name__)
CORS(app)  # Habilita CORS para todas as rotas

# Estado global da aplicação
state = {
    'monitoring': False,
    'monitor_thread': None,
    'stop_flag': False,
    'data_lock': Lock(),
    'current': {
        'download': 0.0,
        'upload': 0.0,
        'ping': 0.0,
        'totalDownload': 0,
        'totalUpload': 0,
        'lastUpdate': None
    },
    'history': [],
    'config': {
        'updateInterval': 5,
        'maxHistoryDays': 30,
        'selectedInterface': '',
        'startWithMonitoring': True
    }
}

# Carregar configuração
def load_config():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                state['config'].update(config)
                logger.info("Configuração carregada com sucesso")
        else:
            save_config()
            logger.info("Arquivo de configuração criado com valores padrão")
    except Exception as e:
        logger.error(f"Erro ao carregar configuração: {e}")

# Salvar configuração
def save_config():
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(state['config'], f, indent=4)
        logger.info("Configuração salva com sucesso")
    except Exception as e:
        logger.error(f"Erro ao salvar configuração: {e}")

# Carregar histórico
def load_history():
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                state['history'] = json.load(f)
                logger.info(f"Histórico carregado com sucesso: {len(state['history'])} registros")
        else:
            state['history'] = []
            save_history()
            logger.info("Arquivo de histórico criado vazio")
    except Exception as e:
        logger.error(f"Erro ao carregar histórico: {e}")
        state['history'] = []

# Salvar histórico
def save_history():
    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(state['history'], f, indent=4)
        logger.info("Histórico salvo com sucesso")
    except Exception as e:
        logger.error(f"Erro ao salvar histórico: {e}")

# Limpar histórico antigo
def clean_old_history():
    if not state['history']:
        return
    
    try:
        max_days = state['config']['maxHistoryDays']
        now = datetime.datetime.now()
        cutoff = now - datetime.timedelta(days=max_days)
        cutoff_timestamp = cutoff.timestamp() * 1000
        
        old_count = len(state['history'])
        state['history'] = [record for record in state['history'] 
                           if record['timestamp'] >= cutoff_timestamp]
        new_count = len(state['history'])
        
        if old_count != new_count:
            logger.info(f"Limpeza de histórico: {old_count - new_count} registros removidos")
            save_history()
    except Exception as e:
        logger.error(f"Erro ao limpar histórico antigo: {e}")

# Obter interfaces de rede
def get_network_interfaces():
    interfaces = []
    
    try:
        if NETIFACES_AVAILABLE:
            # Usa netifaces para obter informações detalhadas
            for iface in netifaces.interfaces():
                try:
                    # Pula interfaces que não têm endereços IP
                    if netifaces.AF_INET not in netifaces.ifaddresses(iface):
                        continue
                    
                    # Obtém o primeiro endereço IPv4
                    ip = netifaces.ifaddresses(iface)[netifaces.AF_INET][0]['addr']
                    
                    # Pula loopback
                    if ip.startswith('127.'):
                        continue
                    
                    interfaces.append({
                        'name': iface,
                        'ip': ip
                    })
                except Exception as e:
                    logger.warning(f"Erro ao processar interface {iface}: {e}")
        else:
            # Fallback para socket se netifaces não estiver disponível
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            interfaces.append({
                'name': 'default',
                'ip': ip
            })
    except Exception as e:
        logger.error(f"Erro ao obter interfaces de rede: {e}")
        # Fallback básico
        interfaces.append({
            'name': 'unknown',
            'ip': '127.0.0.1'
        })
    
    return interfaces

# Executar teste de velocidade
def run_speed_test():
    if not SPEEDTEST_AVAILABLE:
        # Retorna dados simulados se o speedtest não estiver disponível
        logger.info("Gerando resultados simulados de teste de velocidade")
        return {
            'download': random.uniform(10, 100),
            'upload': random.uniform(5, 50),
            'ping': random.uniform(10, 100),
            'server': {
                'name': 'Servidor Simulado',
                'country': 'Brasil',
                'sponsor': 'Simulação'
            }
        }
    
    logger.info("Iniciando teste de velocidade real")
    try:
        s = speedtest.Speedtest()
        s.get_best_server()
        s.download()
        s.upload()
        results = s.results.dict()
        
        return {
            'download': results['download'] / 1_000_000,  # Converte para Mbps
            'upload': results['upload'] / 1_000_000,  # Converte para Mbps
            'ping': results['ping'],
            'server': {
                'name': results['server']['name'],
                'country': results['server']['country'],
                'sponsor': results['server']['sponsor']
            }
        }
    except Exception as e:
        logger.error(f"Erro durante teste de velocidade: {e}")
        # Retorna dados simulados em caso de erro
        return {
            'download': random.uniform(10, 100),
            'upload': random.uniform(5, 50),
            'ping': random.uniform(10, 100),
            'server': {
                'name': 'Erro - Simulado',
                'country': 'Brasil',
                'sponsor': 'Simulação após erro'
            }
        }

# Função de monitoramento que roda em thread separada
def monitor_network(interface=None):
    logger.info(f"Iniciando monitoramento de rede na interface: {interface or 'auto'}")
    
    state['stop_flag'] = False
    last_record_time = 0
    interval = state['config']['updateInterval']
    
    while not state['stop_flag']:
        try:
            # Simula medição de rede (em um aplicativo real, aqui seria implementada a medição real)
            current_time = time.time()
            download_speed = random.uniform(10, 100)  # Mbps
            upload_speed = random.uniform(5, 50)      # Mbps
            ping = random.uniform(10, 100)            # ms
            
            # Calcula dados transferidos desde a última atualização
            time_diff = current_time - last_record_time if last_record_time > 0 else interval
            downloaded = (download_speed * 1_000_000 / 8) * time_diff / 1_000_000  # MB
            uploaded = (upload_speed * 1_000_000 / 8) * time_diff / 1_000_000      # MB
            
            # Atualiza o estado atual
            with state['data_lock']:
                state['current']['download'] = download_speed
                state['current']['upload'] = upload_speed
                state['current']['ping'] = ping
                state['current']['totalDownload'] += downloaded
                state['current']['totalUpload'] += uploaded
                state['current']['lastUpdate'] = current_time
            
            # Registra no histórico a cada intervalo
            if current_time - last_record_time >= 60:  # A cada minuto
                record = {
                    'timestamp': int(current_time * 1000),  # ms
                    'download': download_speed,
                    'upload': upload_speed,
                    'ping': ping,
                    'totalDownload': state['current']['totalDownload'],
                    'totalUpload': state['current']['totalUpload']
                }
                
                with state['data_lock']:
                    state['history'].append(record)
                
                # Salva o histórico
                save_history()
                last_record_time = current_time
                
                # Limpa histórico antigo periodicamente
                if random.random() < 0.1:  # ~10% de chance a cada registro
                    clean_old_history()
            
            time.sleep(interval)
        except Exception as e:
            logger.error(f"Erro durante o monitoramento: {e}")
            time.sleep(interval)
    
    logger.info("Monitoramento de rede finalizado")

# Gerar relatório
def generate_report(report_type='txt'):
    now = datetime.datetime.now()
    date_str = now.strftime('%Y%m%d_%H%M%S')
    filename = f"network_report_{date_str}"
    
    if report_type == 'pdf' and REPORTLAB_AVAILABLE:
        return generate_pdf_report(filename)
    else:
        return generate_text_report(filename)

# Gerar relatório em texto
def generate_text_report(filename):
    try:
        full_path = os.path.join(REPORTS_DIR, f"{filename}.txt")
        
        with open(full_path, 'w') as f:
            f.write("RELATÓRIO DE DESEMPENHO DE REDE\n")
            f.write("==============================\n\n")
            
            # Data e hora
            f.write(f"Gerado em: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
            
            # Informações do sistema
            f.write("INFORMAÇÕES DO SISTEMA\n")
            f.write("---------------------\n")
            f.write(f"Sistema Operacional: {platform.system()} {platform.version()}\n")
            f.write(f"Nome do Host: {socket.gethostname()}\n")
            
            # Estatísticas atuais
            f.write("\nESTATÍSTICAS ATUAIS\n")
            f.write("------------------\n")
            f.write(f"Download: {state['current']['download']:.2f} Mbps\n")
            f.write(f"Upload: {state['current']['upload']:.2f} Mbps\n")
            f.write(f"Ping: {state['current']['ping']:.0f} ms\n")
            f.write(f"Total Downloaded: {format_bytes(state['current']['totalDownload'])}\n")
            f.write(f"Total Uploaded: {format_bytes(state['current']['totalUpload'])}\n")
            
            # Histórico recente
            f.write("\nHISTÓRICO RECENTE (últimas 10 entradas)\n")
            f.write("-------------------------------------\n")
            f.write("Data/Hora            | Download | Upload  | Ping\n")
            f.write("-" * 60 + "\n")
            
            recent_history = sorted(state['history'], key=lambda x: x['timestamp'], reverse=True)[:10]
            for entry in reversed(recent_history):
                entry_time = datetime.datetime.fromtimestamp(entry['timestamp'] / 1000)
                f.write(f"{entry_time.strftime('%d/%m/%Y %H:%M:%S')} | ")
                f.write(f"{entry['download']:7.2f} | ")
                f.write(f"{entry['upload']:7.2f} | ")
                f.write(f"{entry['ping']:4.0f}\n")
        
        # URL relativa para o arquivo
        relative_url = f"/api/reports/download/{filename}.txt"
        
        return {
            'success': True,
            'path': full_path,
            'url': relative_url,
            'filename': f"{filename}.txt"
        }
    except Exception as e:
        logger.error(f"Erro ao gerar relatório de texto: {e}")
        return {
            'success': False, 
            'error': str(e)
        }

# Gerar relatório em PDF
def generate_pdf_report(filename):
    if not REPORTLAB_AVAILABLE:
        logger.warning("Tentativa de gerar PDF sem o ReportLab disponível")
        return {
            'success': False,
            'error': "ReportLab não está instalado. Use o formato de texto."
        }
    
    try:
        full_path = os.path.join(REPORTS_DIR, f"{filename}.pdf")
        
        # Configuração do documento
        doc = SimpleDocTemplate(full_path, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []
        
        # Título
        title_style = styles["Title"]
        elements.append(Paragraph("Relatório de Desempenho de Rede", title_style))
        elements.append(Spacer(1, 12))
        
        # Data e Hora
        date_style = styles["Normal"]
        date_style.alignment = 1  # Centralizado
        elements.append(Paragraph(
            f"Gerado em: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            date_style
        ))
        elements.append(Spacer(1, 20))
        
        # Informações do Sistema
        section_style = styles["Heading2"]
        elements.append(Paragraph("Informações do Sistema", section_style))
        
        system_data = [
            ["Sistema Operacional", f"{platform.system()} {platform.version()}"],
            ["Nome do Host", socket.gethostname()]
        ]
        
        system_table = Table(system_data, colWidths=[200, 300])
        system_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(system_table)
        elements.append(Spacer(1, 20))
        
        # Estatísticas Atuais
        elements.append(Paragraph("Estatísticas Atuais", section_style))
        
        current_data = [
            ["Métrica", "Valor"],
            ["Download", f"{state['current']['download']:.2f} Mbps"],
            ["Upload", f"{state['current']['upload']:.2f} Mbps"],
            ["Ping", f"{state['current']['ping']:.0f} ms"],
            ["Total Downloaded", format_bytes(state['current']['totalDownload'])],
            ["Total Uploaded", format_bytes(state['current']['totalUpload'])]
        ]
        
        current_table = Table(current_data, colWidths=[200, 300])
        current_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(current_table)
        elements.append(Spacer(1, 20))
        
        # Histórico Recente
        elements.append(Paragraph("Histórico Recente", section_style))
        
        history_data = [["Data/Hora", "Download (Mbps)", "Upload (Mbps)", "Ping (ms)"]]
        
        recent_history = sorted(state['history'], key=lambda x: x['timestamp'], reverse=True)[:10]
        for entry in reversed(recent_history):
            entry_time = datetime.datetime.fromtimestamp(entry['timestamp'] / 1000)
            history_data.append([
                entry_time.strftime('%d/%m/%Y %H:%M:%S'),
                f"{entry['download']:.2f}",
                f"{entry['upload']:.2f}",
                f"{entry['ping']:.0f}"
            ])
        
        history_table = Table(history_data, colWidths=[150, 115, 115, 115])
        history_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT')
        ]))
        
        elements.append(history_table)
        
        # Rodapé
        elements.append(Spacer(1, 30))
        footer_style = styles["Normal"]
        footer_style.alignment = 1  # Centralizado
        elements.append(Paragraph(
            "Monitor de Rede - Relatório gerado automaticamente",
            footer_style
        ))
        
        # Gera o PDF
        doc.build(elements)
        
        # URL relativa para o arquivo
        relative_url = f"/api/reports/download/{filename}.pdf"
        
        return {
            'success': True,
            'path': full_path,
            'url': relative_url,
            'filename': f"{filename}.pdf"
        }
    except Exception as e:
        logger.error(f"Erro ao gerar relatório PDF: {e}")
        return {
            'success': False, 
            'error': str(e)
        }

# Formatar bytes para string legível
def format_bytes(size_bytes):
    if size_bytes < 0:
        return "0 B"
    
    size_name = ("B", "KB", "MB", "GB", "TB", "PB")
    i = 0
    while size_bytes >= 1024 and i < len(size_name) - 1:
        size_bytes /= 1024
        i += 1
    
    return f"{size_bytes:.2f} {size_name[i]}"

# Inicializar dados da aplicação
def init_app_data():
    load_config()
    load_history()
    
    # Inicia monitoramento automaticamente se configurado
    if state['config']['startWithMonitoring']:
        start_monitoring()

#
# Rotas da API
#

@app.route('/')
def index():
    """Renderiza a página principal"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """Retorna o status atual do monitoramento"""
    with state['data_lock']:
        return jsonify({
            'success': True,
            'monitoring': state['monitoring'],
            'current': state['current']
        })

@app.route('/api/start', methods=['POST'])
def start_monitoring():
    """Inicia o monitoramento de rede"""
    if state['monitoring']:
        return jsonify({
            'success': False,
            'error': 'Monitoramento já está em andamento'
        })
    
    try:
        data = request.get_json() or {}
        selected_interface = data.get('interface', state['config']['selectedInterface'])
        
        # Inicia a thread de monitoramento
        state['monitor_thread'] = Thread(
            target=monitor_network,
            args=(selected_interface,),
            daemon=True
        )
        state['monitor_thread'].start()
        state['monitoring'] = True
        
        return jsonify({
            'success': True,
            'message': 'Monitoramento iniciado com sucesso'
        })
    except Exception as e:
        logger.error(f"Erro ao iniciar monitoramento: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/stop', methods=['POST'])
def stop_monitoring():
    """Para o monitoramento de rede"""
    if not state['monitoring']:
        return jsonify({
            'success': False,
            'error': 'Monitoramento não está em andamento'
        })
    
    try:
        state['stop_flag'] = True
        state['monitoring'] = False
        
        return jsonify({
            'success': True,
            'message': 'Monitoramento parado com sucesso'
        })
    except Exception as e:
        logger.error(f"Erro ao parar monitoramento: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/reset', methods=['POST'])
def reset_stats():
    """Reseta as estatísticas de rede"""
    try:
        with state['data_lock']:
            state['current']['download'] = 0.0
            state['current']['upload'] = 0.0
            state['current']['ping'] = 0.0
            state['current']['totalDownload'] = 0
            state['current']['totalUpload'] = 0
            state['current']['lastUpdate'] = time.time()
        
        return jsonify({
            'success': True,
            'message': 'Estatísticas resetadas com sucesso'
        })
    except Exception as e:
        logger.error(f"Erro ao resetar estatísticas: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/history')
def get_history():
    """Obtém o histórico de desempenho da rede"""
    try:
        range_param = request.args.get('range', 'day')
        now = datetime.datetime.now()
        
        # Define o período com base no parâmetro
        if range_param == 'week':
            cutoff = now - datetime.timedelta(days=7)
        elif range_param == 'month':
            cutoff = now - datetime.timedelta(days=30)
        else:  # day (default)
            cutoff = now - datetime.timedelta(days=1)
        
        cutoff_timestamp = cutoff.timestamp() * 1000
        
        # Filtra o histórico com base no período
        filtered_history = [record for record in state['history'] 
                            if record['timestamp'] >= cutoff_timestamp]
        
        # Calcula as métricas resumidas
        if filtered_history:
            avg_download = sum(item['download'] for item in filtered_history) / len(filtered_history)
            avg_upload = sum(item['upload'] for item in filtered_history) / len(filtered_history)
            
            # Pega o último registro para os totais
            last_record = max(filtered_history, key=lambda x: x['timestamp'])
            total_download = last_record['totalDownload']
            total_upload = last_record['totalUpload']
        else:
            avg_download = 0
            avg_upload = 0
            total_download = 0
            total_upload = 0
        
        summary = {
            'avgDownload': avg_download,
            'avgUpload': avg_upload,
            'totalDownload': total_download,
            'totalUpload': total_upload
        }
        
        return jsonify({
            'success': True,
            'history': filtered_history,
            'summary': summary
        })
    except Exception as e:
        logger.error(f"Erro ao obter histórico: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/speedtest', methods=['POST'])
def speed_test():
    """Executa um teste de velocidade"""
    try:
        result = run_speed_test()
        
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        logger.error(f"Erro ao executar teste de velocidade: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/config', methods=['GET', 'POST'])
def config():
    """Obtém ou atualiza a configuração"""
    if request.method == 'GET':
        return jsonify({
            'success': True,
            'config': state['config']
        })
    else:  # POST
        try:
            new_config = request.get_json()
            state['config'].update(new_config)
            save_config()
            
            return jsonify({
                'success': True,
                'config': state['config']
            })
        except Exception as e:
            logger.error(f"Erro ao atualizar configuração: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            })

@app.route('/api/interfaces')
def interfaces():
    """Obtém as interfaces de rede disponíveis"""
    try:
        ifaces = get_network_interfaces()
        
        return jsonify({
            'success': True,
            'interfaces': ifaces
        })
    except Exception as e:
        logger.error(f"Erro ao obter interfaces de rede: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/system')
def system_info():
    """Obtém informações do sistema"""
    try:
        sysinfo = {
            'os': f"{platform.system()} {platform.release()}",
            'cpu': platform.processor(),
            'hostname': socket.gethostname(),
            'uptime': time.time()  # Na prática, seria a uptime real do sistema
        }
        
        return jsonify({
            'success': True,
            'system': sysinfo
        })
    except Exception as e:
        logger.error(f"Erro ao obter informações do sistema: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/reports', methods=['GET', 'POST'])
def reports():
    """Gerencia relatórios"""
    if request.method == 'GET':
        try:
            # Lista relatórios existentes
            reports_list = []
            for filename in os.listdir(REPORTS_DIR):
                if not os.path.isfile(os.path.join(REPORTS_DIR, filename)):
                    continue
                
                file_stat = os.stat(os.path.join(REPORTS_DIR, filename))
                report_info = {
                    'name': filename,
                    'date': file_stat.st_mtime * 1000,  # ms
                    'size': file_stat.st_size,
                    'url': f"/api/reports/download/{filename}"
                }
                reports_list.append(report_info)
            
            # Ordena por data, mais recente primeiro
            reports_list.sort(key=lambda x: x['date'], reverse=True)
            
            return jsonify({
                'success': True,
                'reports': reports_list
            })
        except Exception as e:
            logger.error(f"Erro ao listar relatórios: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            })
    else:  # POST
        try:
            # Gera um novo relatório
            report_type = request.args.get('type', 'txt')
            report = generate_report(report_type)
            
            return jsonify({
                'success': report['success'],
                'report': report if report['success'] else None,
                'error': report.get('error')
            })
        except Exception as e:
            logger.error(f"Erro ao gerar relatório: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            })

@app.route('/api/reports/download/<path:filename>')
def download_report(filename):
    """Download de um relatório específico"""
    try:
        return send_from_directory(REPORTS_DIR, filename, as_attachment=True)
    except Exception as e:
        logger.error(f"Erro ao fazer download do relatório: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

# Rota para servir arquivos estáticos (sem precisar do /static no URL)
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(STATIC_DIR, 'icons'), 'favicon.ico')

# Inicialização
def main():
    try:
        init_app_data()
        port = 5000
        if len(sys.argv) > 1:
            try:
                port = int(sys.argv[1])
            except ValueError:
                logger.warning(f"Porta inválida: {sys.argv[1]}. Usando a porta padrão 5000.")
        
        # Em produção, usar waitress ou gunicorn em vez de app.run()
        logger.info(f"Iniciando servidor na porta {port}")
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        logger.error(f"Erro ao iniciar aplicação: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()