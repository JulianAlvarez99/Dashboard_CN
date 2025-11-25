/* static/js/modules/charts.js */

let productionChartInstance = null;
let comparisonChartInstance = null;
let productPieChartInstance = null;

const ZOOM_OPTIONS = {
    pan: { enabled: true, mode: 'x' },
    zoom: { wheel: { enabled: true }, pinch: { enabled: true }, mode: 'x' }
};

export function renderProductionChart(ctx, chartData, options = {}, downtimeEvents = []) {
    if (productionChartInstance) productionChartInstance.destroy();

    // 1. Configuraciones de Dataset
    chartData.datasets.forEach(ds => {
        ds.borderWidth = 2;
        if (options.curveType === 'stepped') {
            ds.stepped = true; ds.tension = 0;
        } else {
            ds.stepped = false; ds.tension = parseFloat(options.curveType || 0.4);
        }
        ds.pointRadius = 0;
        ds.hitRadius = 10;
    });

    // 2. Anotaciones de Parada (Líneas Verticales)
    // Usamos el plugin 'annotation' si está disponible
    const annotations = {};
    if (options.showStops && downtimeEvents.length > 0 && !options.isAllLines) {
        downtimeEvents.forEach((evt, index) => {
            // Línea de Inicio (Roja)
            annotations[`stop_start_${index}`] = {
                type: 'line',
                xMin: evt.start_time,
                xMax: evt.start_time,
                borderColor: 'red',
                borderWidth: 2,
                label: { display: false }
            };
            // Línea de Fin (Verde)
            annotations[`stop_end_${index}`] = {
                type: 'line',
                xMin: evt.end_time,
                xMax: evt.end_time,
                borderColor: 'green',
                borderWidth: 2,
                borderDash: [5, 5], // Punteada para el fin
                label: { display: false }
            };
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
                annotation: { annotations: annotations }, // Inyectar anotaciones
                legend: { position: 'top', labels: { boxWidth: 12, usePointStyle: true } },
                tooltip: { 
                    callbacks: {
                        title: (items) => {
                            return items[0].label; // Mostrar fecha completa
                        }
                    }
                }
            },
            scales: {
                x: { 
                    grid: { display: false },
                    ticks: { 
                        maxRotation: 60, // Rotación solicitada
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
                    backgroundColor: '#3182ce', // Azul
                    order: 2
                },
                { 
                    label: 'Salida', 
                    data: data.exit, 
                    backgroundColor: '#38a169', // Verde
                    order: 2
                },
                { 
                    label: 'Descarte', 
                    data: data.diff, 
                    backgroundColor: '#e53e3e', // Rojo
                    borderColor: '#9b2c2c',
                    borderWidth: 1,
                    // Mostramos descarte como una barra separada pero clara
                    order: 1 
                }
            ]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { zoom: ZOOM_OPTIONS_LOCAL },
            scales: { 
                y: { beginAtZero: true },
                x: { stacked: false } // Barras lado a lado para comparar mejor
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