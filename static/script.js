// Убираем const, используем var или let, чтобы избежать ошибки переопределения
var API_BASE = window.location.origin;

// Функция для получения погоды
function getWeather() {
    console.log('🔍 getWeather() called');
    
    const cityInput = document.getElementById('cityInput');
    const city = cityInput.value.trim();
    
    console.log('🏙️ City:', city);
    
    if (!city) {
        showError('Пожалуйста, введите название города');
        return;
    }

    const resultDiv = document.getElementById('weatherResult');
    const errorDiv = document.getElementById('errorMessage');
    
    // Показываем загрузку
    resultDiv.classList.remove('hidden');
    document.getElementById('cityName').textContent = '⏳ Загрузка...';
    document.getElementById('temperature').textContent = '--°C';
    document.getElementById('humidity').textContent = '💧 Влажность: --%';
    document.getElementById('weatherStatus').innerHTML = '';
    errorDiv.classList.remove('show');

    fetch(`${API_BASE}/weather?city=${encodeURIComponent(city)}`)
        .then(response => {
            console.log('📥 Response status:', response.status);
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.detail || 'Ошибка получения данных'); });
            }
            return response.json();
        })
        .then(data => {
            console.log('✅ Data received:', data);
            
            // Отображаем результат
            document.getElementById('cityName').textContent = data.city;
            document.getElementById('temperature').textContent = data.temperature;
            document.getElementById('humidity').textContent = `💧 Влажность: ${data.humidity}`;
            document.getElementById('weatherStatus').innerHTML = `
                <span class="status-badge">✅ Данные сохранены</span>
            `;
            document.getElementById('currentDate').textContent = new Date().toLocaleString('ru-RU');
            
            // Обновляем историю
            refreshHistory();
        })
        .catch(error => {
            console.error('❌ Error:', error);
            showError(error.message);
            resultDiv.classList.add('hidden');
        });
}

// Функция для обновления истории
function refreshHistory() {
    console.log('🔄 refreshHistory() called');
    
    const container = document.getElementById('historyContainer');
    container.innerHTML = '<div class="loading">Загрузка истории...</div>';
    
    fetch(`${API_BASE}/history?limit=20`)
        .then(response => {
            console.log('📥 History status:', response.status);
            if (!response.ok) {
                throw new Error('Ошибка загрузки истории');
            }
            return response.json();
        })
        .then(data => {
            console.log('📋 History data:', data);
            
            if (data.length === 0) {
                container.innerHTML = '<div class="no-history">📭 История запросов пока пуста</div>';
                return;
            }
            
            let html = '<div class="history-list">';
            data.forEach(item => {
                const date = new Date(item.created_at);
                const formattedDate = date.toLocaleString('ru-RU', {
                    day: '2-digit',
                    month: '2-digit',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });
                
                html += `
                    <div class="history-item">
                        <span class="city">🌍 ${item.city}</span>
                        <div class="weather-data">
                            <span class="temp">🌡️ ${item.temperature}</span>
                            <span class="humid">💧 ${item.humidity}</span>
                            <span class="time">🕐 ${formattedDate}</span>
                        </div>
                    </div>
                `;
            });
            html += '</div>';
            container.innerHTML = html;
        })
        .catch(error => {
            console.error('❌ History error:', error);
            container.innerHTML = `<div class="error-message show">❌ ${error.message}</div>`;
        });
}

// Функция для отображения ошибок
function showError(message) {
    console.error('⚠️ Showing error:', message);
    const errorDiv = document.getElementById('errorMessage');
    errorDiv.textContent = `❌ ${message}`;
    errorDiv.classList.add('show');
}

// Ждем загрузки DOM
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Page loaded');
    
    // Навешиваем обработчики на кнопки
    const searchBtn = document.getElementById('searchBtn');
    const refreshBtn = document.getElementById('refreshBtn');
    const cityInput = document.getElementById('cityInput');
    
    if (searchBtn) {
        searchBtn.addEventListener('click', getWeather);
        console.log('✅ Search button handler attached');
    }
    
    if (refreshBtn) {
        refreshBtn.addEventListener('click', refreshHistory);
        console.log('✅ Refresh button handler attached');
    }
    
    if (cityInput) {
        cityInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                console.log('⌨️ Enter pressed');
                getWeather();
            }
        });
        console.log('✅ City input handler attached');
    }
    
    // Загружаем историю
    refreshHistory();
    
    // Фокус на поле ввода
    cityInput.focus();
});

// Автообновление истории каждые 30 секунд
setInterval(refreshHistory, 30000);

console.log('✅ Script loaded successfully');
