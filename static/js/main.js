/* static/js/main.js */

import { renderProductionChart, renderComparisonChart, renderProductPieChart } from './modules/charts.js'; // Importamos renderComparison
import { updateKPIs, renderDowntimeTable, renderSummaryTable, updateLastUpdatedTime, showLoading } from './modules/ui.js';

// --- CONFIGURACIÓN Y ESTADO ---
document.addEventListener('DOMContentLoaded', () => {
    loadProducts(); // Cargar combo productos
    setupEventListeners();
    
    // Setear fechas por defecto (Hoy)
    resetFilters();
    
    // Carga inicial
    applyFilters();
});

async function loadProducts() {
    try {
        const response = await fetch('/api/products_list');
        const products = await response.json();
        const select = document.getElementById('product-select');
        
        products.forEach(p => {
            const opt = document.createElement('option');
            opt.value = p.id;
            opt.text = p.name;
            select.appendChild(opt);
        });
    } catch (e) {
        console.error("Error cargando productos", e);
    }
}

function setupEventListeners() {
    // Botón Principal
    document.getElementById('btn-filter').addEventListener('click', applyFilters);
    document.getElementById('btn-reset').addEventListener('click', resetFilters);

    // Lógica de Turnos (Cambia las fechas/horas automáticamente)
    document.getElementById('shift-select').addEventListener('change', (e) => {
        handleShiftChange(e.target.value);
    });
}

function handleShiftChange(shift) {
    const dateStart = document.getElementById('date-start');
    const timeStart = document.getElementById('time-start');
    const dateEnd = document.getElementById('date-end');
    const timeEnd = document.getElementById('time-end');
    
    const today = new Date().toISOString().split('T')[0];
    // Para turno noche que termina mañana
    const tomorrowObj = new Date();
    tomorrowObj.setDate(tomorrowObj.getDate() + 1);
    const tomorrow = tomorrowObj.toISOString().split('T')[0];

    switch(shift) {
        case 'morning':
            dateStart.value = today; timeStart.value = "05:00";
            dateEnd.value = today; timeEnd.value = "13:00";
            break;
        case 'afternoon':
            dateStart.value = today; timeStart.value = "13:00";
            dateEnd.value = today; timeEnd.value = "21:00";
            break;
        case 'night':
            dateStart.value = today; timeStart.value = "21:00";
            dateEnd.value = tomorrow; timeEnd.value = "05:00";
            break;
        case 'all':
            dateStart.value = today; timeStart.value = "00:00";
            dateEnd.value = tomorrow; timeEnd.value = "00:00";
            break;
    }
}

function resetFilters() {
    const now = new Date();
    const yesterday = new Date();
    yesterday.setDate(now.getDate() - 1);

    document.getElementById('date-start').value = yesterday.toISOString().split('T')[0];
    document.getElementById('time-start').value = "06:00";
    
    document.getElementById('date-end').value = now.toISOString().split('T')[0];
    document.getElementById('time-end').value = now.getHours().toString().padStart(2, '0') + ":00";
    
    document.getElementById('interval-select').value = '1h';
    document.getElementById('line-select').value = 'ALL';
    document.getElementById('curve-type').value = '0.4';
    document.getElementById('show-stops-check').checked = false;
    
    applyFilters();
}

async function applyFilters() {
    try {
        showLoading(true);

        // 1. Parametros UI
        const startIso = `${document.getElementById('date-start').value}T${document.getElementById('time-start').value}`;
        const endIso = `${document.getElementById('date-end').value}T${document.getElementById('time-end').value}`;
        const interval = document.getElementById('interval-select').value;
        const line = document.getElementById('line-select').value;
        const prodId = document.getElementById('product-select').value;

        // 2. Opciones visuales
        const vizOptions = {
            curveType: document.getElementById('curve-type').value,
            showStops: document.getElementById('show-stops-check').checked,
            displayMode: document.getElementById('display-mode').value
        };

        // 3. Construir URL (CORRECCIÓN: Usamos fetch directo, no api.js)
        let apiUrl = `/api/dashboard?interval=${interval}&start=${startIso}&end=${endIso}`;
        if (line !== 'ALL') apiUrl += `&lines=${line}`;
        if (prodId !== 'ALL') apiUrl += `&product_id=${prodId}`;

        // CORRECCIÓN AQUÍ: Fetch directo
        const response = await fetch(apiUrl);
        
        if (!response.ok) {
            // Intentar leer el error del backend si existe
            const errData = await response.json();
            throw new Error(errData.error || `Error HTTP: ${response.status}`);
        }
        
        const data = await response.json();

        // 4. Actualizar UI
        updateLastUpdatedTime(data.meta.start, data.meta.end);
        updateKPIs(data.kpis); 
        
        renderDowntimeTable(data.downtime.events);
        renderSummaryTable(data.products);

        // 5. Renderizar Gráficos
        const mainCtx = document.getElementById('productionChart').getContext('2d');
        renderProductionChart(mainCtx, data.charts.main, vizOptions, data.downtime.events);
        
        const compCtx = document.getElementById('comparisonChart').getContext('2d');
        renderComparisonChart(compCtx, data.charts.comparison);

        const pieCtx = document.getElementById('productPieChart').getContext('2d');
        renderProductPieChart(pieCtx, data.products);

    } catch (error) {
        console.error("Error en Dashboard:", error);
        alert("Error al cargar datos: " + error.message);
    } finally {
        showLoading(false);
    }
}