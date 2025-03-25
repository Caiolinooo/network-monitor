/**
 * theme.js - Gerenciador de tema claro/escuro para o Monitor de Rede
 * Autor: Caio Valerio Goulart Correia
 * Versão: 1.0.0
 */

(function() {
    // Elementos do DOM
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const themeIconLight = document.getElementById('theme-icon-light');
    const themeIconDark = document.getElementById('theme-icon-dark');
    const themeSelect = document.getElementById('theme-select');
    
    // Nome da chave para armazenamento local
    const THEME_STORAGE_KEY = 'network-monitor-theme-preference';
    
    // Temas disponíveis
    const THEMES = {
        LIGHT: 'light',
        DARK: 'dark',
        AUTO: 'auto'
    };
    
    /**
     * Obtém o tema atual do elemento body
     * @returns {string} O tema atual
     */
    function getCurrentTheme() {
        return document.body.getAttribute('data-theme') || THEMES.LIGHT;
    }
    
    /**
     * Define o tema no documento e atualiza os ícones
     * @param {string} theme - O tema a ser aplicado (light/dark)
     */
    function setTheme(theme) {
        document.body.setAttribute('data-theme', theme);
        
        // Atualiza os ícones do botão de alternância
        if (theme === THEMES.DARK) {
            themeIconLight.classList.remove('show');
            themeIconDark.classList.add('show');
        } else {
            themeIconLight.classList.add('show');
            themeIconDark.classList.remove('show');
        }
        
        // Salva a preferência no localStorage se não for definição automática temporária
        if (getSavedThemePreference() !== THEMES.AUTO) {
            localStorage.setItem(THEME_STORAGE_KEY, theme);
        }
    }
    
    /**
     * Alterna entre os temas claro e escuro
     */
    function toggleTheme() {
        const currentTheme = getCurrentTheme();
        const newTheme = currentTheme === THEMES.LIGHT ? THEMES.DARK : THEMES.LIGHT;
        
        setTheme(newTheme);
        
        // Se tivermos um seletor de tema na página de configurações, atualize-o
        if (themeSelect) {
            themeSelect.value = newTheme;
        }
        
        // Salva a preferência no localStorage (não mais automático)
        localStorage.setItem(THEME_STORAGE_KEY, newTheme);
    }
    
    /**
     * Obtém a preferência de tema salva
     * @returns {string} A preferência de tema salva ou AUTO se não existir
     */
    function getSavedThemePreference() {
        return localStorage.getItem(THEME_STORAGE_KEY) || THEMES.AUTO;
    }
    
    /**
     * Detecta se o sistema do usuário prefere tema escuro
     * @returns {boolean} Verdadeiro se o sistema preferir tema escuro
     */
    function prefersColorSchemeDark() {
        return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
    
    /**
     * Aplica o tema com base na preferência salva ou configuração do sistema
     */
    function applyThemePreference() {
        const savedPreference = getSavedThemePreference();
        
        if (savedPreference === THEMES.AUTO) {
            // Configuração automática baseada no sistema
            const systemPreference = prefersColorSchemeDark() ? THEMES.DARK : THEMES.LIGHT;
            setTheme(systemPreference);
        } else {
            // Usar preferência salva explicitamente pelo usuário
            setTheme(savedPreference);
        }
        
        // Atualiza o seletor na página de configurações se existir
        if (themeSelect) {
            themeSelect.value = savedPreference;
        }
    }
    
    // Inicializa o tema
    applyThemePreference();
    
    // Adiciona o manipulador de eventos ao botão de alternância de tema
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', toggleTheme);
    }
    
    // Adiciona o manipulador de eventos ao seletor de tema se existir
    if (themeSelect) {
        themeSelect.addEventListener('change', function() {
            const selectedTheme = themeSelect.value;
            
            if (selectedTheme === THEMES.AUTO) {
                // Limpa a preferência explícita e usa a configuração do sistema
                localStorage.setItem(THEME_STORAGE_KEY, THEMES.AUTO);
                const systemPreference = prefersColorSchemeDark() ? THEMES.DARK : THEMES.LIGHT;
                setTheme(systemPreference);
            } else {
                // Define o tema explicitamente
                setTheme(selectedTheme);
                localStorage.setItem(THEME_STORAGE_KEY, selectedTheme);
            }
        });
    }
    
    // Adiciona listener para alterações na preferência de cor do sistema
    if (window.matchMedia) {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
            // Só altera automaticamente se a preferência estiver como AUTO
            if (getSavedThemePreference() === THEMES.AUTO) {
                setTheme(e.matches ? THEMES.DARK : THEMES.LIGHT);
            }
        });
    }
})();