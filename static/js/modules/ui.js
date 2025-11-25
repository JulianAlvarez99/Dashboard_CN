/**
 * Módulo encargado de manipular el DOM (HTML)
 */

// Formateador de Fecha y Hora (dd/mm/yyyy HH:mm)
const dateTimeFmt = new Intl.DateTimeFormat('es-AR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit', hour12: false
});

const timeFmt = new Intl.DateTimeFormat('es-AR', {
    hour: '2-digit', minute: '2-digit', hour12: false
});

export function updateKPIs(kpis) {
    const formatNum = (n) => n.toLocaleString('es-AR');
    
    document.getElementById('kpi-output').innerText = formatNum(kpis.total_output);
    document.getElementById('kpi-downtime-count').innerText = kpis.downtime_count;
    document.getElementById('kpi-downtime-time').innerText = kpis.downtime_total_str; // Ya viene HH:MM:SS del backend
}

export function updateLastUpdatedTime(startIso, endIso) {
    const s = dateTimeFmt.format(new Date(startIso));
    const e = dateTimeFmt.format(new Date(endIso));
    document.getElementById('last-update').innerText = `Datos: ${s} al ${e}`;
}

export function renderSummaryTable(products) {
    const tbody = document.getElementById('summary-table-body');
    tbody.innerHTML = '';
    
    // Ordenar por cantidad desc
    products.sort((a,b) => b.cantidad - a.cantidad);

    products.forEach(p => {
        // Limpieza de nombre
        const name = p.product_name.replace(/_/g, ' ');
        const row = `
            <tr>
                <td>
                    <span style="display:inline-block;width:10px;height:10px;background-color:${p.color};border-radius:50%;margin-right:5px;"></span>
                    ${name}
                </td>
                <td class="text-end fw-bold">${p.cantidad.toLocaleString()}</td>
                <td class="text-end text-muted">${p.percent}%</td>
            </tr>
        `;
        tbody.innerHTML += row;
    });
}

// Función auxiliar para limpiar el string de python "0 days 00:40:54"
function cleanDuration(durationStr) {
    // Si viene como "0 days 00:40:54", quitamos el "0 days " y los segundos si queremos
    // Una forma simple es usar Regex o split
    if (!durationStr) return "--";
    
    // Quitamos "0 days " si existe
    let clean = durationStr.replace('0 days ', '');
    
    // clean ahora es "00:40:54" o "11:38:53"
    const parts = clean.split(':');
    if (parts.length === 3) {
        return `${parseInt(parts[0])}h ${parseInt(parts[1])}m`; // Ej: 11h 38m
    }
    return clean;
}

export function renderDowntimeTable(events) {
    const tbody = document.getElementById('downtime-table-body');
    tbody.innerHTML = '';

    if (!events.length) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">Sin paradas</td></tr>';
        return;
    }

    events.forEach(evt => {
        // Formato limpio de duración
        const dur = evt.duration_formatted.replace('0 days ', '').split('.')[0];
        // Formato fecha dd/mm HH:mm
        const start = dateTimeFmt.format(new Date(evt.start_time));
        const end = timeFmt.format(new Date(evt.end_time)); // Solo hora fin

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

export function showLoading(isLoading) {
    // Opcional: Mostrar spinner global o cambiar opacidad
    document.body.style.cursor = isLoading ? 'wait' : 'default';
    const btn = document.getElementById('btn-filter');
    if(btn) btn.disabled = isLoading;
}