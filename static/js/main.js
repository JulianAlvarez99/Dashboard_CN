/* static/js/main.js */

import { renderProductionChart, renderComparisonChart, renderProductPieChart } from './modules/charts.js';
import { updateKPIs, renderDowntimeTable, renderSummaryTable, updateLastUpdatedTime, showLoading } from './modules/ui.js';

/**
 * Inicialización de la aplicación.
 */
document.addEventListener('DOMContentLoaded', () => {
    loadProducts(); 
    setupEventListeners();
    setInitialDefaults(); 
});

/**
 * Carga la lista de productos para poblar el filtro select.
 */
async function loadProducts() {
    try {
        const response = await fetch('/api/products_list');
        const products = await response.json();
        const select = document.getElementById('product-select');
        
        // Resetear opción default
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

/**
 * Configura los listeners de los botones y controles.
 */
function setupEventListeners() {
    document.getElementById('btn-filter').addEventListener('click', applyFilters);
    
    // Placeholder para futura funcionalidad de PDF
    document.getElementById('btn-pdf').addEventListener('click', () => {
        alert("Funcionalidad de PDF pendiente de implementación.");
    });
    
    // Nota: Eliminado el listener de cambio de turno que modificaba las fechas
    // Ahora el turno actúa como un filtro transparente.
}

/**
 * Establece los valores por defecto en los inputs (Ayer -> Hoy).
 */
function setInitialDefaults() {
    const now = new Date();
    const yesterday = new Date(now);
    yesterday.setDate(yesterday.getDate() - 1);

    // Fechas: Ayer 06:00 a Hoy 06:00
    document.getElementById('date-start').value = yesterday.toISOString().split('T')[0];
    document.getElementById('time-start').value = "06:00";
    
    document.getElementById('date-end').value = now.toISOString().split('T')[0];
    document.getElementById('time-end').value = "06:00";
    
    // Valores por defecto de UI
    document.getElementById('interval-select').value = '1h';
    document.getElementById('line-select').value = 'ALL';
    document.getElementById('product-select').value = 'ALL';
    document.getElementById('curve-type').value = 'stepped'; 
    document.getElementById('show-stops-check').checked = false;
    
    // No llamamos a applyFilters() aquí para iniciar con dashboard vacío
}

/**
 * Recopila filtros, llama a la API y orquesta el renderizado.
 */
async function applyFilters() {
    try {
        showLoading(true);

        // 1. Recopilación de Parámetros del DOM
        const startIso = `${document.getElementById('date-start').value}T${document.getElementById('time-start').value}`;
        const endIso = `${document.getElementById('date-end').value}T${document.getElementById('time-end').value}`;
        const interval = document.getElementById('interval-select').value;
        const line = document.getElementById('line-select').value;
        const prodId = document.getElementById('product-select').value;
        const shift = document.getElementById('shift-select').value;

        // 2. Opciones de Visualización (No van a la API)
        const vizOptions = {
            curveType: document.getElementById('curve-type').value,
            showStops: document.getElementById('show-stops-check').checked,
            displayMode: document.getElementById('display-mode').value,
            isAllLines: line === 'ALL'
        };

        // 3. Construcción de URL para la API
        // Usamos fetch nativo aquí para control total de los parámetros complejos
        let apiUrl = `/api/dashboard?interval=${interval}&start=${startIso}&end=${endIso}`;
        
        if (line !== 'ALL') apiUrl += `&lines=${line}`;
        if (prodId !== 'ALL') apiUrl += `&product_id=${prodId}`;
        if (shift !== 'all') apiUrl += `&shift=${shift}`;

        // 4. Petición de Datos
        const response = await fetch(apiUrl);
        
        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.error || `Error HTTP: ${response.status}`);
        }
        
        const data = await response.json();

        // 5. Gestión de Estado de la UI (Mostrar contenedores ocultos)
        document.getElementById('empty-state').style.display = 'none';
        document.getElementById('kpi-container').style.display = 'flex';
        document.getElementById('charts-container').style.display = 'block';

        // Si vemos todas las líneas, ocultamos detalle de paradas (es confuso mezclarlas)
        const downtimeElements = document.querySelectorAll('.downtime-card-group, .downtime-list-section');
        downtimeElements.forEach(el => {
            el.style.display = vizOptions.isAllLines ? 'none' : 'block';
        });

        // 6. Renderizado de Componentes
        updateLastUpdatedTime(data.meta.start, data.meta.end);
        updateKPIs(data.kpis); 
        
        if (!vizOptions.isAllLines) {
            renderDowntimeTable(data.downtime.events);
        }
        
        renderSummaryTable(data.products);

        // Renderizar Gráficos
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