    /**
     * Busca informações do sistema
     */
    function fetchSystemInfo() {
        fetch(API.BASE_URL + API.ENDPOINTS.SYSTEM)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    AppState.systemInfo = data.system;
                    updateSystemInfo();
                }
            })
            .catch(error => {
                console.error('Erro ao obter informações do sistema:', error);
            });
    }

    /**
     * Atualiza as informações do sistema na UI
     */
    function updateSystemInfo() {
        if (DOM.dashboard.systemOS) {
            DOM.dashboard.systemOS.textContent = AppState.systemInfo.os || '-';
        }
        
        if (DOM.dashboard.systemCPU) {
            DOM.dashboard.systemCPU.textContent = AppState.systemInfo.cpu || '-';
        }
        
        if (DOM.dashboard.systemMemory) {
            DOM.dashboard.systemMemory.textContent = formatMemory(AppState.systemInfo.memory) || '-';
        }
        
        if (DOM.dashboard.systemUptime) {
            DOM.dashboard.systemUptime.textContent = formatUptime(AppState.systemInfo.uptime) || '-';
        }
    }

    /**
     * Busca interfaces de rede disponíveis
     */
    function fetchInterfaces() {
        fetch(API.BASE_URL + API.ENDPOINTS.INTERFACES)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    AppState.interfaces = data.interfaces;
                    updateInterfaceSelect();
                }
            })
            .catch(error => {
                console.error('Erro ao obter interfaces de rede:', error);
            });
    }

    /**
     * Atualiza o seletor de interfaces
     */
    function updateInterfaceSelect() {
        if (DOM.settings.interfaceSelect) {
            // Limpa opções existentes, exceto a primeira (Auto-detectar)
            while (DOM.settings.interfaceSelect.options.length > 1) {
                DOM.settings.interfaceSelect.remove(1);
            }
            
            // Adiciona as interfaces como opções
            AppState.interfaces.forEach(iface => {
                const option = document.createElement('option');
                option.value = iface.name;
                option.textContent = `${iface.name} (${iface.ip || 'Sem IP'})`;
                DOM.settings.interfaceSelect.appendChild(option);
            });
            
            // Seleciona a interface atual se estiver definida
            if (AppState.settings.selectedInterface) {
                DOM.settings.interfaceSelect.value = AppState.settings.selectedInterface;
            }
        }
    }

    /**
     * Busca relatórios disponíveis
     */
    function fetchReports() {
        fetch(API.BASE_URL + API.ENDPOINTS.REPORTS)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateReportsList(data.reports);
                }
            })
            .catch(error => {
                console.error('Erro ao obter relatórios:', error);
            });
    }

    /**
     * Atualiza a lista de relatórios na UI
     */
    function updateReportsList(reports) {
        if (DOM.reports.reportsContainer) {
            if (reports && reports.length > 0) {
                // Limpa o conteúdo existente
                DOM.reports.reportsContainer.innerHTML = '';
                
                // Adiciona cada relatório à lista
                reports.forEach(report => {
                    const reportItem = document.createElement('div');
                    reportItem.className = 'report-item';
                    
                    const reportInfo = document.createElement('div');
                    reportInfo.className = 'report-info';
                    
                    const reportTitle = document.createElement('div');
                    reportTitle.className = 'report-title';
                    reportTitle.textContent = report.name;
                    
                    const reportDate = document.createElement('div');
                    reportDate.className = 'report-date';
                    reportDate.textContent = new Date(report.date).toLocaleString();
                    
                    reportInfo.appendChild(reportTitle);
                    reportInfo.appendChild(reportDate);
                    
                    const reportActions = document.createElement('div');
                    reportActions.className = 'report-actions';
                    
                    const downloadBtn = document.createElement('a');
                    downloadBtn.href = report.url;
                    downloadBtn.className = 'btn secondary';
                    downloadBtn.textContent = 'Download';
                    downloadBtn.setAttribute('download', '');
                    
                    reportActions.appendChild(downloadBtn);
                    
                    reportItem.appendChild(reportInfo);
                    reportItem.appendChild(reportActions);
                    
                    DOM.reports.reportsContainer.appendChild(reportItem);
                });
            } else {
                // Exibe mensagem de nenhum relatório
                DOM.reports.reportsContainer.innerHTML = '<p class="empty-state">Nenhum relatório gerado recentemente.</p>';
            }
        }
    }

    /**
     * Busca o status atual do monitor
     */
    function fetchStatus() {
        fetch(API.BASE_URL + API.ENDPOINTS.STATUS)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateUI(data);
                    
                    // Verifica se o monitoramento está ativo
                    if (data.monitoring) {
                        AppState.isMonitoring = true;
                        updateMonitoringControls(true);
                    } else {
                        AppState.isMonitoring = false;
                        updateMonitoringControls(false);
                    }
                }
            })
            .catch(error => {
                console.error('Erro ao obter status:', error);
                stopPolling();
                updateMonitoringControls(false);
            });
    }

    /**
     * Atualiza a UI com os dados recebidos
     */
    function updateUI(data) {
        // Atualiza os valores atuais
        if (data.current) {
            AppState.data.current = data.current;
            
            if (DOM.dashboard.currentDownload) {
                DOM.dashboard.currentDownload.textContent = data.current.download.toFixed(2);
            }
            
            if (DOM.dashboard.currentUpload) {
                DOM.dashboard.currentUpload.textContent = data.current.upload.toFixed(2);
            }
            
            if (DOM.dashboard.currentPing) {
                DOM.dashboard.currentPing.textContent = Math.round(data.current.ping);
            }
            
            if (DOM.dashboard.totalDownload) {
                DOM.dashboard.totalDownload.textContent = formatBytes(data.current.totalDownload);
            }
            
            if (DOM.dashboard.totalUpload) {
                DOM.dashboard.totalUpload.textContent = formatBytes(data.current.totalUpload);
            }
            
            // Atualiza o gráfico de velocidade
            if (AppState.charts.speedChart) {
                const chart = AppState.charts.speedChart;
                const timestamp = new Date().toLocaleTimeString();
                
                // Adiciona novos dados
                chart.data.labels.push(timestamp);
                chart.data.datasets[0].data.push(data.current.download);
                chart.data.datasets[1].data.push(data.current.upload);
                
                // Limita o número de pontos visíveis
                if (chart.data.labels.length > 20) {
                    chart.data.labels.shift();
                    chart.data.datasets[0].data.shift();
                    chart.data.datasets[1].data.shift();
                }
                
                // Atualiza o gráfico
                chart.update();
            }
        }
    }