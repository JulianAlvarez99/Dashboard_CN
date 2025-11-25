/* static/js/main.js */

import { renderProductionChart, renderComparisonChart, renderProductPieChart } from './modules/charts.js';
import { updateKPIs, renderDowntimeTable, renderSummaryTable, updateLastUpdatedTime, showLoading } from './modules/ui.js';

document.addEventListener('DOMContentLoaded', () => {
    loadProducts(); 
    setupEventListeners();
    setInitialDefaults(); // Setea fechas pero NO carga datos
});

async function loadProducts() {
    try {
        const response = await fetch('/api/products_list');
        const products = await response.json();
        const select = document.getElementById('product-select');
        select.innerHTML = '<option value="ALL">Todos</option>';
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
    document.getElementById('btn-filter').addEventListener('click', applyFilters);
    document.getElementById('btn-pdf').addEventListener('click', () => alert("Funcionalidad de PDF pendiente de implementación."));
}

function setInitialDefaults() {
    // Configuración por defecto: Ayer 06:00 a Hoy 06:00
    const now = new Date();
    const yesterday = new Date(now);
    yesterday.setDate(yesterday.getDate() - 1);

    document.getElementById('date-start').value = yesterday.toISOString().split('T')[0];
    document.getElementById('time-start').value = "06:00";
    
    document.getElementById('date-end').value = now.toISOString().split('T')[0];
    document.getElementById('time-end').value = "06:00";
    
    document.getElementById('interval-select').value = '1h';
    document.getElementById('line-select').value = 'ALL';
    document.getElementById('product-select').value = 'ALL';
    document.getElementById('curve-type').value = 'stepped'; // Por defecto Escalonada
    document.getElementById('show-stops-check').checked = false;
}

function handleShiftChange(shift) {
    const dateStart = document.getElementById('date-start');
    const timeStart = document.getElementById('time-start');
    const dateEnd = document.getElementById('date-end');
    const timeEnd = document.getElementById('time-end');
    
    // Obtenemos la fecha que esté seleccionada actualmente en el "Inicio" como base
    let baseDate = new Date(dateStart.value);
    if (isNaN(baseDate)) baseDate = new Date();
    
    const baseDateStr = baseDate.toISOString().split('T')[0];
    
    // Para turno noche, si empieza hoy, termina mañana
    const nextDay = new Date(baseDate);
    nextDay.setDate(nextDay.getDate() + 1);
    const nextDayStr = nextDay.toISOString().split('T')[0];

    switch(shift) {
        case 'morning': // 06:00 - 14:00
            dateStart.value = baseDateStr; timeStart.value = "06:00";
            dateEnd.value = baseDateStr;   timeEnd.value = "14:00";
            break;
        case 'afternoon': // 14:00 - 22:00
            dateStart.value = baseDateStr; timeStart.value = "14:00";
            dateEnd.value = baseDateStr;   timeEnd.value = "22:00";
            break;
        case 'night': // 22:00 - 06:00 (del día siguiente)
            dateStart.value = baseDateStr; timeStart.value = "22:00";
            dateEnd.value = nextDayStr;    timeEnd.value = "06:00";
            break;
        case 'all': // 06:00 a 06:00 del día sig (Jornada completa)
            dateStart.value = baseDateStr; timeStart.value = "06:00";
            dateEnd.value = nextDayStr;    timeEnd.value = "06:00";
            break;
    }
}

async function applyFilters() {
    try {
        showLoading(true);

        const startIso = `${document.getElementById('date-start').value}T${document.getElementById('time-start').value}`;
        const endIso = `${document.getElementById('date-end').value}T${document.getElementById('time-end').value}`;
        const interval = document.getElementById('interval-select').value;
        const line = document.getElementById('line-select').value;
        const prodId = document.getElementById('product-select').value;
        const shift = document.getElementById('shift-select').value;

        // Opciones visuales
        const vizOptions = {
            curveType: document.getElementById('curve-type').value,
            showStops: document.getElementById('show-stops-check').checked,
            displayMode: document.getElementById('display-mode').value,
            isAllLines: line === 'ALL'
        };

        // Construir URL
        let apiUrl = `/api/dashboard?interval=${interval}&start=${startIso}&end=${endIso}`;
        if (line !== 'ALL') apiUrl += `&lines=${line}`;
        if (prodId !== 'ALL') apiUrl += `&product_id=${prodId}`;
        if (shift !== 'all') apiUrl += `&shift=${shift}`;

        const response = await fetch(apiUrl);
        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.error || `Error HTTP: ${response.status}`);
        }
        
        const data = await response.json();

        // Mostrar contenedores
        document.getElementById('empty-state').style.display = 'none';
        document.getElementById('kpi-container').style.display = 'flex';
        document.getElementById('charts-container').style.display = 'block';

        // Gestión de visibilidad de Paradas (Si son todas las líneas, se ocultan)
        const downtimeElements = document.querySelectorAll('.downtime-card-group, .downtime-list-section');
        downtimeElements.forEach(el => {
            el.style.display = vizOptions.isAllLines ? 'none' : 'block';
        });

        // Actualizar UI
        updateLastUpdatedTime(data.meta.start, data.meta.end);
        updateKPIs(data.kpis); 
        
        if (!vizOptions.isAllLines) {
            renderDowntimeTable(data.downtime.events);
        }
        
        renderSummaryTable(data.products);

        // Renderizar Gráficos
        const mainCtx = document.getElementById('productionChart').getContext('2d');
        // Pasamos las labels del gráfico para que el renderer pueda alinear las paradas
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