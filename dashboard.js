document.addEventListener('DOMContentLoaded', () => {
    console.log("🚀 MONETRA System Booted Successfully...");
    fetchDashboardData();
    setInterval(fetchDashboardData, 60000); // Tepat 1 menit sekali
});

async function fetchDashboardData() {
    try {
        const cacheBuster = new Date().getTime();
        const response = await fetch(`/api/data?_t=${cacheBuster}`);
        
        if (!response.ok) throw new Error(`HTTP Error Status: ${response.status}`);
        const data = await response.json();

        if (data.latest) {
            updateCard('air_temp', data.latest.air_temp);
            updateCard('humidity', data.latest.humidity);
            updateCard('air_pressure', data.latest.air_pressure);
            updateCard('wind_speed', data.latest.wind_speed);
            updateCard('rain', data.latest.rain);
            updateCard('water_level', data.latest.water_level);

            const syncTimeElem = document.getElementById('sync-time');
            if (syncTimeElem && data.latest.timestamp) {
                syncTimeElem.innerText = data.latest.timestamp;
            }
        }

        renderAlerts(data.alerts);
        renderTable(data.history_logs);

    } catch (error) {
        console.error('❌ Gagal sinkronisasi data frontend:', error);
    }
}

function updateCard(elementId, value) {
    let aliases = [];
    if (elementId === 'air_temp') aliases = ['air_temp', 'suhu', 'suhu_udara', 'temp'];
    else if (elementId === 'humidity') aliases = ['humidity', 'kelembapan', 'kelembaban', 'hum'];
    else if (elementId === 'air_pressure') aliases = ['air_pressure', 'tekanan', 'tekanan_udara', 'press'];
    else if (elementId === 'wind_speed') aliases = ['wind_speed', 'kec_angin', 'kecepatan_angin', 'wind'];
    else if (elementId === 'rain') aliases = ['rain', 'curah_hujan', 'hujan'];
    else if (elementId === 'water_level') aliases = ['water_level', 'tinggi_air', 'waterlevel', 'tma'];
    else aliases = [elementId];

    let elem = null;
    for (let alias of aliases) {
        elem = document.getElementById(alias);
        if (elem) break; 
    }

    if (elem) {
        // 🚀 Format nilai angka lengkap dengan satuannya masing-masing
        let formattedValue = '--';
        if (value !== undefined && value !== null) {
            if (elementId === 'air_temp') formattedValue = `${value} °C`;
            else if (elementId === 'humidity') formattedValue = `${value} %`;
            else if (elementId === 'air_pressure') formattedValue = `${value} hPa`;
            else if (elementId === 'wind_speed') formattedValue = `${value} knots`;
            else if (elementId === 'rain') formattedValue = `${value} mm`;
            else if (elementId === 'water_level') formattedValue = `${value} m`;
            else formattedValue = value;
        }
        
        elem.innerText = formattedValue;
        
        // Suntikkan Teks Batas Aman BMKG di bagian bawah kartu
        const parentCard = elem.closest('.card') || elem.parentElement;
        if (parentCard) {
            const limitText = parentCard.querySelector('.bmkg-limit');
            if (limitText) {
                if (elementId === 'air_temp') limitText.innerText = 'Batas BMKG: 20 - 40 °C';
                if (elementId === 'humidity') limitText.innerText = 'Batas BMKG: 30 - 100 %';
                if (elementId === 'air_pressure') limitText.innerText = 'Batas BMKG: 1006 - 1016 hPa';
                if (elementId === 'wind_speed') limitText.innerText = 'Batas BMKG: 0 - 20 knots';
                if (elementId === 'rain') limitText.innerText = 'Batas BMKG: 0 - 300 mm';
                if (elementId === 'water_level') limitText.innerText = 'Batas BMKG: 0 - 3 m';
            }
        }
    }
}

function renderAlerts(alerts) {
    const alertContainer = document.getElementById('alert-container');
    if (!alertContainer) return;
    alertContainer.innerHTML = '';
    if (alerts && alerts.length > 0) {
        alerts.forEach(alertText => {
            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert alert-warning mb-2';
            alertDiv.style.backgroundColor = '#fff3cd';
            alertDiv.style.borderLeft = '5px solid #ffc107';
            alertDiv.style.padding = '10px 15px';
            alertDiv.innerHTML = `<strong>⚠️ ${alertText}</strong>`;
            alertContainer.appendChild(alertDiv);
        });
    }
}

function renderTable(logs) {
    const tableBody = document.getElementById('history-table-body');
    if (!tableBody) return;

    if (!logs || logs.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-muted">Menunggu sinkronisasi data dari server BMKG...</td></tr>`;
        return;
    }

    tableBody.innerHTML = '';
    logs.forEach(log => {
        const isAnomaly = log.status === 'Anomali Sensor';
        const badgeClass = isAnomaly ? 'bg-warning text-dark' : 'bg-success text-white';
        const badgeText = isAnomaly ? '⚠️ Anomali' : '✓ Normal';

        const row = `
            <tr>
                <td class="text-primary fw-bold">${log.timestamp}</td>
                <td>${log.air_temp}</td>
                <td>${log.humidity}</td>
                <td>${log.air_pressure}</td>
                <td>${log.wind_speed}</td>
                <td>${log.rain}</td>
                <td>${log.water_level}</td>
                <td><span class="badge ${badgeClass}" style="padding: 6px 12px; border-radius: 12px;">${badgeText}</span></td>
            </tr>
        `;
        tableBody.innerHTML += row;
    });
}