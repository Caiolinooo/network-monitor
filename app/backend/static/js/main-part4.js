    /**
     * Inicia o monitoramento
     */
    function startMonitoring() {
        fetch(API.BASE_URL + API.ENDPOINTS.START, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                interface: AppState.settings.selectedInterface
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                AppState.isMonitoring = true;
                updateMonitoringControls(true);
                startPolling();
                showToast('Monitoramento iniciado com sucesso!', 'success');
            } else {
                showToast('Erro ao iniciar monitoramento: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Erro ao iniciar monitoramento:', error);
            showToast('Erro ao iniciar monitoramento', 'error');
        });
    }

    /**
     * Para o monitoramento
     */
    function stopMonitoring() {
        fetch(API.BASE_URL + API.ENDPOINTS.STOP, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                AppState.isMonitoring = false;
                updateMonitoringControls(false);
                stopPolling();
                showToast('Monitoramento parado com sucesso!', 'success');
            } else {
                showToast('Erro ao parar monitoramento: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Erro ao parar monitoramento:', error);
            showToast('Erro ao parar monitoramento', 'error');
        });
    }

    /**
     * Reseta as estatísticas
     */
    function resetStats() {
        fetch(API.BASE_URL + API.ENDPOINTS.RESET, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Reinicia os valores
                if (AppState.charts.speedChart) {
                    AppState.charts.speedChart.data.labels = [];
                    AppState.charts.speedChart.data.datasets[0].data = [];
                    AppState.charts.speedChart.data.datasets[1].data = [];
                    AppState.charts.speedChart.update();
                }
                
                // Atualiza com os novos valores zerados
                fetchStatus();
                showToast('Estatísticas resetadas com sucesso!', 'success');
            } else {
                showToast('Erro ao resetar estatísticas: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Erro ao resetar estatísticas:', error);
            showToast('Erro ao resetar estatísticas', 'error');
        });
    }

    /**
     * Busca o histórico para o período selecionado
     */
    function fetchHistory() {
        const range = DOM.history.rangeSelect ? DOM.history.rangeSelect.value : 'day';
        
        fetch(`${API.BASE_URL}${API.ENDPOINTS.HISTORY}?range=${range}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateHistoryChart(data.history);
                    updateHistorySummary(data.summary);
                }
            })
            .catch(error => {
                console.error('Erro ao obter histórico:', error);
                showToast('Erro ao carregar dados do histórico', 'error');
            });
    }

    /**
     * Atualiza o gráfico de histórico
     */
    function updateHistoryChart(history) {
        if (AppState.charts.historyChart && history) {
            const chart = AppState.charts.historyChart;
            
            // Prepara dados para o gráfico
            const labels = history.map(item => formatDateTime(item.timestamp));
            const downloadData = history.map(item => item.download);
            const uploadData = history.map(item => item.upload);
            const pingData = history.map(item => item.ping);
            
            // Atualiza o gráfico
            chart.data.labels = labels;
            chart.data.datasets[0].data = downloadData;
            chart.data.datasets[1].data = uploadData;
            chart.data.datasets[2].data = pingData;
            
            chart.update();
        }
    }

    /**
     * Atualiza o resumo do histórico
     */
    function updateHistorySummary(summary) {
        if (summary) {
            if (DOM.history.totalDownload) {
                DOM.history.totalDownload.textContent = formatBytes(summary.totalDownload);
            }
            
            if (DOM.history.totalUpload) {
                DOM.history.totalUpload.textContent = formatBytes(summary.totalUpload);
            }
            
            if (DOM.history.avgDownload) {
                DOM.history.avgDownload.textContent = summary.avgDownload.toFixed(2) + ' Mbps';
            }
            
            if (DOM.history.avgUpload) {
                DOM.history.avgUpload.textContent = summary.avgUpload.toFixed(2) + ' Mbps';
            }
        }
    }

    /**
     * Inicia um teste de velocidade
     */
    function startSpeedTest() {
        // Desabilita o botão durante o teste
        if (DOM.speedTest.startBtn) {
            DOM.speedTest.startBtn.disabled = true;
            DOM.speedTest.startBtn.textContent = 'Executando teste...';
        }
        
        // Reseta os valores
        if (DOM.speedTest.downloadValue) DOM.speedTest.downloadValue.textContent = '--';
        if (DOM.speedTest.uploadValue) DOM.speedTest.uploadValue.textContent = '--';
        if (DOM.speedTest.pingValue) DOM.speedTest.pingValue.textContent = '--';
        if (DOM.speedTest.serverName) DOM.speedTest.serverName.textContent = '-';
        
        // Inicia a barra de progresso
        startProgressBar();
        
        // Faz a chamada API
        fetch(API.BASE_URL + API.ENDPOINTS.SPEEDTEST, {
            method: 'POST'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Erro na resposta do servidor');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Atualiza os valores com o resultado
                if (DOM.speedTest.downloadValue) {
                    DOM.speedTest.downloadValue.textContent = data.result.download.toFixed(2);
                }
                
                if (DOM.speedTest.uploadValue) {
                    DOM.speedTest.uploadValue.textContent = data.result.upload.toFixed(2);
                }
                
                if (DOM.speedTest.pingValue) {
                    DOM.speedTest.pingValue.textContent = Math.round(data.result.ping);
                }
                
                if (DOM.speedTest.serverName) {
                    DOM.speedTest.serverName.textContent = data.result.server.name || '-';
                }
                
                if (DOM.speedTest.lastTestTime) {
                    DOM.speedTest.lastTestTime.textContent = new Date().toLocaleString();
                }
                
                showToast('Teste de velocidade concluído com sucesso!', 'success');
            } else {
                showToast('Erro durante o teste de velocidade: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Erro ao executar teste de velocidade:', error);
            showToast('Erro ao executar o teste de velocidade', 'error');
        })
        .finally(() => {
            // Reativa o botão
            if (DOM.speedTest.startBtn) {
                DOM.speedTest.startBtn.disabled = false;
                DOM.speedTest.startBtn.textContent = 'Iniciar Teste';
            }
            
            // Conclui a barra de progresso
            completeProgressBar();
        });
    }