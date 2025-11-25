/* static/js/modules/charts.js */

let productionChartInstance = null;
let comparisonChartInstance = null;
let productPieChartInstance = null;

// Configuración común de Zoom
const ZOOM_OPTIONS = {
    pan: { enabled: true, mode: 'x' },
    zoom: {
        wheel: { enabled: true },
        pinch: { enabled: true },
        mode: 'x',
    }
};

// Colores (Light Theme compatible)
const LINE_COLORS = {
    'linea_1': '#3182ce', // Azul fuerte
    'linea_2': '#38a169', // Verde
    'linea_3': '#d53f8c', // Rosa
    'TOTAL PLANTA': '#e53e3e' // Rojo
};

export function renderProductionChart(ctx, chartData, options = {}, downtimeEvents = []) {
    if (productionChartInstance) productionChartInstance.destroy();

    // Configurar datasets (Productos)
    chartData.datasets.forEach(ds => {
        // El color ya viene del backend (ds.borderColor)
        ds.borderWidth = 2;
        
        // Tipo de Curva
        if (options.curveType === 'stepped') {
            ds.stepped = true; ds.tension = 0;
        } else {
            ds.stepped = false; ds.tension = parseFloat(options.curveType || 0.4);
        }
        ds.pointRadius = 0;
        ds.hitRadius = 10; // Facilita el hover
    });

    // Marcadores de Parada (Scatter)
    if (options.showStops && downtimeEvents.length > 0) {
        const stopPoints = downtimeEvents.map(evt => ({
            x: evt.start_time, y: 0, line: evt.line, duration: evt.duration_formatted
        }));
        chartData.datasets.push({
            label: 'Paradas', data: stopPoints, type: 'scatter',
            backgroundColor: '#e53e3e', pointStyle: 'triangle', pointRadius: 8, order: 0
        });
    }

    productionChartInstance = new Chart(ctx, {
        type: 'line',
        data: { labels: chartData.labels, datasets: chartData.datasets },
        options: {
            responsive: true, maintainAspectRatio: false,
            interaction: { mode: 'nearest', axis: 'x', intersect: false },
            plugins: {
                zoom: ZOOM_OPTIONS, // Activar Zoom
                legend: { position: 'top', labels: { boxWidth: 12, usePointStyle: true } },
                tooltip: {
                    callbacks: {
                        label: (ctx) => ctx.dataset.label === 'Paradas' ? `${ctx.raw.line}: ${ctx.raw.duration}` : `${ctx.dataset.label}: ${ctx.parsed.y}`
                    }
                }
            },
            scales: {
                x: { grid: { display: false }, ticks: { maxRotation: 0, autoSkip: true } },
                y: { beginAtZero: true }
            }
        }
    });
}

export function renderComparisonChart(ctx, data) {
    if (comparisonChartInstance) comparisonChartInstance.destroy();

    // Definir opciones de zoom localmente si no están globales
    const ZOOM_OPTIONS = {
        pan: { enabled: true, mode: 'x' },
        zoom: { wheel: { enabled: true }, pinch: { enabled: true }, mode: 'x' }
    };

    comparisonChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [
                { label: 'Entrada', data: data.entry, backgroundColor: '#3182ce' },
                { label: 'Salida', data: data.exit, backgroundColor: '#38a169' },
                { 
                    label: 'Descarte (Calc)', 
                    data: data.diff, 
                    backgroundColor: '#e53e3e', 
                    type: 'line', 
                    borderColor: '#e53e3e', 
                    borderDash: [5,5], 
                    fill: false,
                    pointRadius: 0
                }
            ]
        },
        options: {
            responsive: true, 
            maintainAspectRatio: false,
            plugins: { zoom: ZOOM_OPTIONS },
            scales: { y: { beginAtZero: true } }
        }
    });
}

export function renderProductPieChart(ctx, productsData) {
    if (productPieChartInstance) productPieChartInstance.destroy();
    // ... (Tu lógica de torta existente) ...
    // Asegúrate de usar productsData que ya trae nombres y colores
    const labels = productsData.map(p => p.product_name.replace(/_/g, ' '));
    const values = productsData.map(p => p.cantidad);
    const colors = productsData.map(p => p.color);

    productPieChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: { labels: labels, datasets: [{ data: values, backgroundColor: colors }] },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false } }, // Ocultamos leyenda porque hay tabla al lado
            cutout: '70%'
        }
    });
}

// Escuchar evento global para resetear zoom
document.addEventListener('reset-chart-zoom', () => {
    if (productionChartInstance) productionChartInstance.resetZoom();
    if (comparisonChartInstance) comparisonChartInstance.resetZoom();
});