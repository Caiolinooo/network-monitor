/**
 * main.js - Script principal para a interface do Monitor de Rede
 * Autor: Caio Valerio Goulart Correia
 * Versão: 1.0.0
 */

(function() {
    // Constantes da API
    const API = {
        BASE_URL: '',
        ENDPOINTS: {
            STATUS: '/api/status',
            HISTORY: '/api/history',
            SPEEDTEST: '/api/speedtest',
            CONFIG: '/api/config',
            START: '/api/start',
            STOP: '/api/stop',
            RESET: '/api/reset',
            INTERFACES: '/api/interfaces',
            SYSTEM: '/api/system',
            REPORTS: '/api/reports'
        },
        POLL_INTERVAL: 5000, // 5 segundos por padrão
    };

    // Estado da Aplicação
    const AppState = {
        isMonitoring: false,
        pollingInterval: null,
        lastUpdate: null,
        data: {
            current: {
                download: 0,
                upload: 0,
                ping: 0,
                totalDownload: 0,
                totalUpload: 0
            },
            history: []
        },
        charts: {},
        systemInfo: {},
        interfaces: [],
        settings: {
            updateInterval: 5,
            maxHistoryDays: 30,
            selectedInterface: '',
            startWithMonitoring: true,
            theme: 'auto'
        }
    };

    // Elementos DOM
    const DOM = {
        navLinks: document.querySelectorAll('.main-nav a'),
        sections: document.querySelectorAll('.content-section'),
        dashboard: {
            currentDownload: document.getElementById('current-download'),
            currentUpload: document.getElementById('current-upload'),
            currentPing: document.getElementById('current-ping'),
            totalDownload: document.getElementById('total-download'),
            totalUpload: document.getElementById('total-upload'),
            startBtn: document.getElementById('start-monitoring'),
            stopBtn: document.getElementById('stop-monitoring'),
            resetBtn: document.getElementById('reset-stats'),
            speedChart: document.getElementById('speed-chart'),
            systemOS: document.getElementById('system-os'),
            systemCPU: document.getElementById('system-cpu'),
            systemMemory: document.getElementById('system-memory'),
            systemUptime: document.getElementById('system-uptime')
        },
        history: {
            rangeSelect: document.getElementById('history-range'),
            historyChart: document.getElementById('history-chart'),
            totalDownload: document.getElementById('history-total-download'),
            totalUpload: document.getElementById('history-total-upload'),
            avgDownload: document.getElementById('history-avg-download'),
            avgUpload: document.getElementById('history-avg-upload')
        },
        speedTest: {
            startBtn: document.getElementById('start-speed-test'),
            downloadValue: document.querySelector('.speed-meter:nth-child(1) .meter-value'),
            uploadValue: document.querySelector('.speed-meter:nth-child(2) .meter-value'),
            pingValue: document.querySelector('.speed-meter:nth-child(3) .meter-value'),
            serverName: document.getElementById('server-name'),
            lastTestTime: document.getElementById('last-test-time'),
            progressBar: document.getElementById('speed-test-progress'),
            progressInner: document.querySelector('#speed-test-progress .progress-inner')
        },
        settings: {
            form: document.getElementById('settings-form'),
            updateInterval: document.getElementById('update-interval'),
            maxHistoryDays: document.getElementById('max-history-days'),
            interfaceSelect: document.getElementById('interface-select'),
            themeSelect: document.getElementById('theme-select'),
            startWithMonitoring: document.getElementById('start-with-monitoring')
        },
        reports: {
            generatePDFBtn: document.getElementById('generate-report-pdf'),
            generateTXTBtn: document.getElementById('generate-report-txt'),
            reportsContainer: document.getElementById('reports-container')
        },
        modal: {
            aboutModal: document.getElementById('about-modal'),
            openAboutBtn: document.getElementById('open-about'),
            closeBtn: document.querySelector('.close-modal')
        }
    };

    /**
     * Inicializa a aplicação
     */
    function initApp() {
        setupEventListeners();
        setupCharts();
        loadSettings();
        fetchSystemInfo();
        fetchInterfaces();
        fetchReports();
        
        // Busca o status inicial
        fetchStatus();
    }

    /**
     * Configura todos os event listeners
     */
    function setupEventListeners() {
        // Navegação
        DOM.navLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const targetSection = this.getAttribute('data-section');
                
                // Atualiza as classes
                DOM.navLinks.forEach(link => link.classList.remove('active'));
                this.classList.add('active');
                
                DOM.sections.forEach(section => section.classList.remove('active'));
                document.getElementById(targetSection).classList.add('active');
                
                // Carrega dados adicionais se necessário
                if (targetSection === 'history') {
                    fetchHistory();
                } else if (targetSection === 'reports') {
                    fetchReports();
                }
            });
        });
        
        // Botões de controle do Dashboard
        if (DOM.dashboard.startBtn) {
            DOM.dashboard.startBtn.addEventListener('click', startMonitoring);
        }
        
        if (DOM.dashboard.stopBtn) {
            DOM.dashboard.stopBtn.addEventListener('click', stopMonitoring);
        }
        
        if (DOM.dashboard.resetBtn) {
            DOM.dashboard.resetBtn.addEventListener('click', resetStats);
        }
        
        // Configurações de Histórico
        if (DOM.history.rangeSelect) {
            DOM.history.rangeSelect.addEventListener('change', fetchHistory);
        }
        
        // Controle de Teste de Velocidade
        if (DOM.speedTest.startBtn) {
            DOM.speedTest.startBtn.addEventListener('click', startSpeedTest);
        }
        
        // Formulário de Configurações
        if (DOM.settings.form) {
            DOM.settings.form.addEventListener('submit', function(e) {
                e.preventDefault();
                saveSettings();
            });
        }
        
        // Geração de Relatórios
        if (DOM.reports.generatePDFBtn) {
            DOM.reports.generatePDFBtn.addEventListener('click', function() {
                generateReport('pdf');
            });
        }
        
        if (DOM.reports.generateTXTBtn) {
            DOM.reports.generateTXTBtn.addEventListener('click', function() {
                generateReport('txt');
            });
        }
        
        // Modal Sobre
        if (DOM.modal.openAboutBtn) {
            DOM.modal.openAboutBtn.addEventListener('click', function(e) {
                e.preventDefault();
                DOM.modal.aboutModal.style.display = 'block';
            });
        }
        
        if (DOM.modal.closeBtn) {
            DOM.modal.closeBtn.addEventListener('click', function() {
                DOM.modal.aboutModal.style.display = 'none';
            });
        }
        
        // Fechar o modal ao clicar fora
        window.addEventListener('click', function(e) {
            if (e.target === DOM.modal.aboutModal) {
                DOM.modal.aboutModal.style.display = 'none';
            }
        });
    }