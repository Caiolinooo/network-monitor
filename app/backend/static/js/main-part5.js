    /**
     * Salva as configurações
     */
    function saveSettings() {
        // Obtém os valores do formulário
        const settings = {
            updateInterval: parseInt(DOM.settings.updateInterval.value) || 5,
            maxHistoryDays: parseInt(DOM.settings.maxHistoryDays.value) || 30,
            selectedInterface: DOM.settings.interfaceSelect.value,
            startWithMonitoring: DOM.settings.startWithMonitoring.checked,
            theme: DOM.settings.themeSelect.value
        };
        
        // Atualiza o estado local
        AppState.settings = settings;
        
        // Salva no localStorage
        localStorage.setItem('network-monitor-settings', JSON.stringify(settings));
        
        // Atualiza o intervalo de polling
        API.POLL_INTERVAL = settings.updateInterval * 1000;
        
        // Envia para o servidor
        fetch(API.BASE_URL + API.ENDPOINTS.CONFIG, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(settings)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Configurações salvas com sucesso!', 'success');
            } else {
                showToast('Erro ao salvar configurações: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Erro ao salvar configurações:', error);
            showToast('Erro ao salvar configurações', 'error');
        });
    }

    /**
     * Gera um relatório
     */
    function generateReport(type) {
        fetch(`${API.BASE_URL}${API.ENDPOINTS.REPORTS}?type=${type}`, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Relatório gerado com sucesso!', 'success');
                // Atualiza a lista de relatórios
                fetchReports();
                
                // Se tiver URL para download, abre automaticamente
                if (data.report && data.report.url) {
                    window.open(data.report.url, '_blank');
                }
            } else {
                showToast('Erro ao gerar relatório: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Erro ao gerar relatório:', error);
            showToast('Erro ao gerar relatório', 'error');
        });
    }

    /**
     * Inicia o polling para obter atualizações
     */
    function startPolling() {
        if (AppState.pollingInterval) {
            clearInterval(AppState.pollingInterval);
        }
        
        AppState.pollingInterval = setInterval(() => {
            fetchStatus();
        }, API.POLL_INTERVAL);
    }

    /**
     * Para o polling
     */
    function stopPolling() {
        if (AppState.pollingInterval) {
            clearInterval(AppState.pollingInterval);
            AppState.pollingInterval = null;
        }
    }

    /**
     * Atualiza os controles de monitoramento na UI
     */
    function updateMonitoringControls(isMonitoring) {
        if (DOM.dashboard.startBtn) {
            DOM.dashboard.startBtn.disabled = isMonitoring;
        }
        
        if (DOM.dashboard.stopBtn) {
            DOM.dashboard.stopBtn.disabled = !isMonitoring;
        }
    }

    /**
     * Inicia a animação da barra de progresso
     */
    function startProgressBar() {
        if (DOM.speedTest.progressInner) {
            DOM.speedTest.progressInner.style.width = '0%';
            
            // Simula progresso incremental
            let progress = 0;
            const progressInterval = setInterval(() => {
                // Avança mais rápido no início, mais lento no final
                const step = progress < 50 ? 5 : (progress < 80 ? 3 : 1);
                progress += step;
                
                if (progress >= 95) {
                    clearInterval(progressInterval);
                    progress = 95; // Deixa em 95% até completar
                }
                
                DOM.speedTest.progressInner.style.width = progress + '%';
            }, 500);
            
            // Guarda a referência do intervalo
            AppState.progressInterval = progressInterval;
        }
    }

    /**
     * Completa a barra de progresso
     */
    function completeProgressBar() {
        if (DOM.speedTest.progressInner) {
            // Limpa o intervalo existente
            if (AppState.progressInterval) {
                clearInterval(AppState.progressInterval);
            }
            
            // Completa para 100%
            DOM.speedTest.progressInner.style.width = '100%';
            
            // Após completar, esconde a barra
            setTimeout(() => {
                DOM.speedTest.progressInner.style.width = '0%';
            }, 1500);
        }
    }

    /**
     * Exibe uma mensagem toast
     */
    function showToast(message, type = 'info') {
        // Verifica se já existe um toast container
        let toastContainer = document.querySelector('.toast-container');
        
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container';
            document.body.appendChild(toastContainer);
        }
        
        // Cria o toast
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        // Adiciona ao container
        toastContainer.appendChild(toast);
        
        // Adiciona classe para mostrar com animação
        setTimeout(() => {
            toast.classList.add('show');
        }, 10);
        
        // Remove após 3 segundos
        setTimeout(() => {
            toast.classList.remove('show');
            
            // Remove do DOM após a animação
            setTimeout(() => {
                toast.remove();
                
                // Se não há mais toasts, remove o container
                if (toastContainer.children.length === 0) {
                    toastContainer.remove();
                }
            }, 300);
        }, 3000);
    }

    // Funções Utilitárias

    /**
     * Formata bytes para unidades legíveis
     */
    function formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 B';
        
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(decimals)) + ' ' + sizes[i];
    }

    /**
     * Formata a memória em GB
     */
    function formatMemory(memoryMB) {
        if (!memoryMB) return '-';
        return (memoryMB / 1024).toFixed(2) + ' GB';
    }

    /**
     * Formata o tempo de atividade
     */
    function formatUptime(seconds) {
        if (!seconds) return '-';
        
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        
        let result = '';
        
        if (days > 0) {
            result += days + 'd ';
        }
        
        if (hours > 0 || days > 0) {
            result += hours + 'h ';
        }
        
        result += minutes + 'm';
        
        return result;
    }

    /**
     * Formata data e hora
     */
    function formatDateTime(timestamp) {
        if (!timestamp) return '-';
        
        const date = new Date(timestamp);
        return date.toLocaleString();
    }

    // Inicializa a aplicação quando o DOM estiver pronto
    document.addEventListener('DOMContentLoaded', initApp);
})();