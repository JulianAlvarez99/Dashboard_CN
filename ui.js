/**
 * Módulo de Interfaz de Usuario (UI).
 * Encargado de manipular el DOM, actualizar textos, tablas y spinners.
 */

// --- CONSTANTES Y FORMATEADORES ---

// Formateador de Fecha y Hora (ej: 24/11/2025 14:30)
const dateTimeFmt = new Intl.DateTimeFormat('es-AR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit', hour12: false
});

// Formateador solo Hora (ej: 14:30)
const timeFmt = new Intl.DateTimeFormat('es-AR', {
    hour: '2-digit', minute: '2-digit', hour12: false
});

// Formateador de Números (separador de miles)
const numFmt = new Intl.NumberFormat('es-AR');

// --- FUNCIONES EXPORTADAS ---

/**
 * Actualiza las tarjetas de indicadores (KPIs) en el DOM.
 * @param {Object} kpis - Objeto con los valores calculados (output, downtime, weight).
 */
export function updateKPIs(kpis) {
    // Actualizar Producción
    const elOutput = document.getElementById('kpi-output');
    if (elOutput) elOutput.innerText = numFmt.format(kpis.total_output);

    // Actualizar Conteo de Paradas
    const elCount = document.getElementById('kpi-downtime-count');
    if (elCount) elCount.innerText = kpis.downtime_count;

    // Actualizar Tiempo Total
    const elTime = document.getElementById('kpi-downtime-time');
    if (elTime) elTime.innerText = kpis.downtime_total_str;

    // Actualizar Peso (Verificamos existencia por si se oculta la tarjeta)
    const elWeight = document.getElementById('kpi-weight');
    if (elWeight) elWeight.innerText = kpis.total_weight_kg + " kg";
}

/**
 * Actualiza el texto de "Última actualización" o rango de fechas visible.
 * @param {string} startIso - Fecha inicio en formato ISO.
 * @param {string} endIso - Fecha fin en formato ISO.
 */
export function updateLastUpdatedTime(startIso, endIso) {
    const s = dateTimeFmt.format(new Date(startIso));
    const e = dateTimeFmt.format(new Date(endIso));
    const el = document.getElementById('last-update');
    if (el) el.innerText = `Datos visualizados: ${s} al ${e}`;
}

/**
 * Renderiza la tabla resumen de distribución de productos.
 * @param {Array} products - Lista de objetos producto con nombre, cantidad, color y porcentaje.
 */
export function renderSummaryTable(products) {
    const tbody = document.getElementById('summary-table-body');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    // Ordenar por cantidad descendente para mostrar los más importantes arriba
    products.sort((a, b) => b.cantidad - a.cantidad);

    products.forEach(p => {
        const name = p.product_name.replace(/_/g, ' ');
        
        // Creamos la fila con el indicador de color visual (círculo)
        const row = `
            <tr>
                <td>
                    <span style="display:inline-block; width:12px; height:12px; background-color:${p.color}; border-radius:50%; margin-right:8px; border:1px solid #ccc;"></span>
                    ${name}
                </td>
                <td class="text-end fw-bold">${numFmt.format(p.cantidad)}</td>
                <td class="text-end text-muted">${p.percent}%</td>
            </tr>
        `;
        tbody.innerHTML += row;
    });
}

/**
 * Renderiza la tabla detallada de paradas.
 * @param {Array} events - Lista de eventos de parada.
 */
export function renderDowntimeTable(events) {
    const tbody = document.getElementById('downtime-table-body');
    if (!tbody) return;

    tbody.innerHTML = '';

    if (!events || events.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted py-3">Sin paradas registradas en este período</td></tr>';
        return;
    }

    events.forEach(evt => {
        // Limpiar string de duración ("0 days 00:40:00" -> "00:40:00")
        const dur = evt.duration_formatted.replace('0 days ', '').split('.')[0];
        const start = dateTimeFmt.format(new Date(evt.start_time));
        const end = timeFmt.format(new Date(evt.end_time)); // Solo hora para el fin por espacio

        const row = `
            <tr>
                <td><span class="badge bg-dark">${evt.line}</span></td>
                <td>${start}</td>
                <td>${end}</td>
                <td class="text-danger fw-bold">${dur}</td>
            </tr>
        `;
        tbody.innerHTML += row;
    });
}

/**
 * Muestra u oculta indicadores de carga (Spinner o estado de botones).
 * @param {boolean} isLoading - True para activar estado de carga.
 */
export function showLoading(isLoading) {
    document.body.style.cursor = isLoading ? 'wait' : 'default';
    const btn = document.getElementById('btn-filter');
    if (btn) {
        btn.disabled = isLoading;
        btn.innerHTML = isLoading ? 
            '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Cargando...' : 
            '🔄 Actualizar Dashboard';
    }
}