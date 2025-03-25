    /**
     * Configura os gráficos da aplicação
     */
    function setupCharts() {
        // Configuração para o gráfico de velocidade do Dashboard
        if (DOM.dashboard.speedChart) {
            const ctx = DOM.dashboard.speedChart.getContext('2d');
            
            // Dados iniciais vazios
            const data = {
                labels: [],
                datasets: [
                    {
                        label: 'Download (Mbps)',
                        data: [],
                        borderColor: 'rgba(0, 120, 215, 1)',
                        backgroundColor: 'rgba(0, 120, 215, 0.1)',
                        pointRadius: 2,
                        pointHoverRadius: 5,
                        borderWidth: 2,
                        fill: true,
                        tension: 0.3
                    },
                    {
                        label: 'Upload (Mbps)',
                        data: [],
                        borderColor: 'rgba(0, 183, 74, 1)',
                        backgroundColor: 'rgba(0, 183, 74, 0.1)',
                        pointRadius: 2,
                        pointHoverRadius: 5,
                        borderWidth: 2,
                        fill: true,
                        tension: 0.3
                    }
                ]
            };
            
            // Opções do gráfico
            const options = {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            maxTicksLimit: 8
                        }
                    },
                    y: {
                        beginAtZero: true,
                        suggestedMax: 10
                    }
                },
                animation: {
                    duration: 800
                },
                plugins: {
                    legend: {
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                }
            };
            
            // Cria o gráfico
            AppState.charts.speedChart = new Chart(ctx, {
                type: 'line',
                data: data,
                options: options
            });
        }
        
        // Configuração para o gráfico de histórico
        if (DOM.history.historyChart) {
            const ctx = DOM.history.historyChart.getContext('2d');
            
            // Dados iniciais vazios
            const data = {
                labels: [],
                datasets: [
                    {
                        label: 'Download (Mbps)',
                        data: [],
                        borderColor: 'rgba(0, 120, 215, 1)',
                        backgroundColor: 'rgba(0, 120, 215, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.3
                    },
                    {
                        label: 'Upload (Mbps)',
                        data: [],
                        borderColor: 'rgba(0, 183, 74, 1)',
                        backgroundColor: 'rgba(0, 183, 74, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.3
                    },
                    {
                        label: 'Ping (ms)',
                        data: [],
                        borderColor: 'rgba(255, 143, 0, 1)',
                        backgroundColor: 'rgba(255, 143, 0, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.3,
                        yAxisID: 'y1'
                    }
                ]
            };
            
            // Opções do gráfico
            const options = {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        grid: {
                            display: true,
                            color: 'rgba(200, 200, 200, 0.2)'
                        },
                        ticks: {
                            maxTicksLimit: 12
                        }
                    },
                    y: {
                        beginAtZero: true,
                        suggestedMax: 10,
                        title: {
                            display: true,
                            text: 'Velocidade (Mbps)'
                        }
                    },
                    y1: {
                        beginAtZero: true,
                        suggestedMax: 100,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Ping (ms)'
                        },
                        grid: {
                            display: false
                        }
                    }
                },
                animation: {
                    duration: 1000
                },
                plugins: {
                    legend: {
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                }
            };
            
            // Cria o gráfico
            AppState.charts.historyChart = new Chart(ctx, {
                type: 'line',
                data: data,
                options: options
            });
        }
    }

    /**
     * Carrega as configurações salvas
     */
    function loadSettings() {
        // Tenta obter as configurações do localStorage
        const savedSettings = localStorage.getItem('network-monitor-settings');
        
        if (savedSettings) {
            try {
                const parsedSettings = JSON.parse(savedSettings);
                AppState.settings = { ...AppState.settings, ...parsedSettings };
                
                // Atualiza os campos do formulário
                if (DOM.settings.updateInterval) {
                    DOM.settings.updateInterval.value = AppState.settings.updateInterval;
                }
                
                if (DOM.settings.maxHistoryDays) {
                    DOM.settings.maxHistoryDays.value = AppState.settings.maxHistoryDays;
                }
                
                if (DOM.settings.startWithMonitoring) {
                    DOM.settings.startWithMonitoring.checked = AppState.settings.startWithMonitoring;
                }
                
                if (DOM.settings.themeSelect) {
                    DOM.settings.themeSelect.value = AppState.settings.theme;
                }
                
                // Atualiza o intervalo de polling
                API.POLL_INTERVAL = AppState.settings.updateInterval * 1000;
                
                // Se configurado para iniciar com monitoramento, inicia-o
                if (AppState.settings.startWithMonitoring) {
                    setTimeout(() => {
                        startMonitoring();
                    }, 1000);
                }
            } catch (error) {
                console.error('Erro ao carregar configurações:', error);
            }
        } else {
            // Se não há configurações salvas, obtem-as da API
            fetch(API.BASE_URL + API.ENDPOINTS.CONFIG)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        AppState.settings = { ...AppState.settings, ...data.config };
                        
                        // Atualiza os campos do formulário
                        if (DOM.settings.updateInterval) {
                            DOM.settings.updateInterval.value = AppState.settings.updateInterval;
                        }
                        
                        if (DOM.settings.maxHistoryDays) {
                            DOM.settings.maxHistoryDays.value = AppState.settings.maxHistoryDays;
                        }
                        
                        if (DOM.settings.startWithMonitoring) {
                            DOM.settings.startWithMonitoring.checked = AppState.settings.startWithMonitoring;
                        }
                        
                        if (DOM.settings.themeSelect) {
                            DOM.settings.themeSelect.value = AppState.settings.theme;
                        }
                        
                        // Atualiza o intervalo de polling
                        API.POLL_INTERVAL = AppState.settings.updateInterval * 1000;
                        
                        // Se configurado para iniciar com monitoramento, inicia-o
                        if (AppState.settings.startWithMonitoring) {
                            setTimeout(() => {
                                startMonitoring();
                            }, 1000);
                        }
                    }
                })
                .catch(error => {
                    console.error('Erro ao obter configurações:', error);
                });
        }
    }