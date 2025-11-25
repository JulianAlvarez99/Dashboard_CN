/* static/js/modules/charts.js */

let productionChartInstance = null;
let comparisonChartInstance = null;
let productPieChartInstance = null;

const ZOOM_OPTIONS = {
    pan: { enabled: true, mode: 'x' },
    zoom: { wheel: { enabled: true }, pinch: { enabled: true }, mode: 'x' }
};

// Función auxiliar para crear colores transparentes
function hexToRgba(hex, alpha) {
    if (!hex || !hex.startsWith('#')) return hex;
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

export function renderProductionChart(ctx, chartData, options = {}, downtimeEvents = []) {
    if (productionChartInstance) productionChartInstance.destroy();

    // 1. Configurar Datasets (Estilo Área Transparente)
    chartData.datasets.forEach(ds => {
        ds.borderWidth = 2;
        
        // Convertir color de borde a relleno transparente (20%)
        if (ds.borderColor && ds.borderColor.startsWith('#')) {
            ds.backgroundColor = hexToRgba(ds.borderColor, 0.2);
            ds.fill = true; 
        }

        // Configuración de Curva
        if (options.curveType === 'stepped') {
            ds.stepped = true; ds.tension = 0;
        } else {
            ds.stepped = false; ds.tension = parseFloat(options.curveType || 0.4);
        }
        
        ds.pointRadius = 0;
        ds.hitRadius = 10;
    });

    // 2. Lógica de Anotaciones (Marcas de Parada con Etiquetas)
    const annotations = {};
    if (options.showStops && downtimeEvents.length > 0 && !options.isAllLines) {
        downtimeEvents.forEach((evt, index) => {
            
            // Strings de fecha para buscar coincidencia en el eje X
            const stopTimeStr = new Date(evt.start_time).toLocaleString('es-AR', {day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit', hour12:false}).replace(',', '');
            const restartTimeStr = new Date(evt.end_time).toLocaleString('es-AR', {day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit', hour12:false}).replace(',', '');
            
            // Buscar índices aproximados
            const startIndex = chartData.labels.findIndex(l => l >= stopTimeStr);
            const endIndex = chartData.labels.findIndex(l => l >= restartTimeStr);

            // --- MARCA DE INICIO (ROJA) ---
            if (startIndex !== -1) {
                annotations[`stop_start_${index}`] = {
                    type: 'line',
                    scaleID: 'x',
                    value: chartData.labels[startIndex],
                    borderColor: '#e53e3e', // Rojo
                    borderWidth: 2,
                    label: {
                        display: true,
                        content: 'Inicio',
                        position: 'start', // Arriba
                        backgroundColor: 'rgba(229, 62, 62, 0.8)',
                        color: 'white',
                        font: { size: 10 },
                        yAdjust: 0 // Posición vertical
                    }
                };
            }

            // --- MARCA DE FIN (VERDE) ---
            if (endIndex !== -1) {
                annotations[`stop_end_${index}`] = {
                    type: 'line',
                    scaleID: 'x',
                    value: chartData.labels[endIndex],
                    borderColor: '#38a169', // Verde
                    borderWidth: 2,
                    borderDash: [5, 5],
                    label: {
                        display: true,
                        content: 'Fin',
                        position: 'start', // Arriba
                        backgroundColor: 'rgba(56, 161, 105, 0.8)',
                        color: 'white',
                        font: { size: 10 },
                        yAdjust: 20 // Un poco más abajo para no solaparse con "Inicio" si es corto
                    }
                };
            }
        });
    }

    productionChartInstance = new Chart(ctx, {
        type: 'line',
        data: { labels: chartData.labels, datasets: chartData.datasets },
        options: {
            responsive: true, maintainAspectRatio: false,
            interaction: { mode: 'nearest', axis: 'x', intersect: false },
            plugins: {
                zoom: ZOOM_OPTIONS,
                annotation: { annotations: annotations },
                legend: { position: 'top', labels: { boxWidth: 12, usePointStyle: true } },
                tooltip: { 
                    callbacks: {
                        title: (items) => items[0].label
                    }
                }
            },
            scales: {
                x: { 
                    grid: { display: false },
                    ticks: { 
                        maxRotation: 60,
                        minRotation: 60,
                        autoSkip: true 
                    } 
                },
                y: { beginAtZero: true }
            }
        }
    });
}

export function renderComparisonChart(ctx, data) {
    if (comparisonChartInstance) comparisonChartInstance.destroy();

    const ZOOM_OPTIONS_LOCAL = {
        pan: { enabled: true, mode: 'x' },
        zoom: { wheel: { enabled: true }, pinch: { enabled: true }, mode: 'x' }
    };

    comparisonChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [
                { 
                    label: 'Entrada', 
                    data: data.entry, 
                    backgroundColor: '#3182ce', 
                    stack: 'Stack 0', 
                    order: 1
                },
                { 
                    label: 'Salida', 
                    data: data.exit, 
                    backgroundColor: '#38a169', 
                    stack: 'Stack 1', 
                    order: 1
                },
                { 
                    label: 'Descarte', 
                    data: data.diff, 
                    backgroundColor: '#e53e3e', 
                    stack: 'Stack 1', 
                    order: 1
                }
            ]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { 
                zoom: ZOOM_OPTIONS_LOCAL,
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: { 
                y: { beginAtZero: true, title: { display: true, text: 'Bolsas' } },
                x: { 
                    stacked: true, 
                    ticks: { maxRotation: 60, minRotation: 60, autoSkip: true }
                } 
            }
        }
    });
}

export function renderProductPieChart(ctx, productsData) {
    if (productPieChartInstance) productPieChartInstance.destroy();

    const labels = productsData.map(p => p.product_name.replace(/_/g, ' '));
    const values = productsData.map(p => p.cantidad);
    const colors = productsData.map(p => p.color);

    productPieChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: { labels: labels, datasets: [{ data: values, backgroundColor: colors }] },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false } }, 
            cutout: '60%'
        }
    });
}

document.addEventListener('reset-chart-zoom', () => {
    if (productionChartInstance) productionChartInstance.resetZoom();
    if (comparisonChartInstance) comparisonChartInstance.resetZoom();
});