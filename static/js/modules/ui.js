/* static/js/modules/ui.js */

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
    document.getElementById('kpi-downtime-time').innerText = kpis.downtime_total_str;
    const kpiWeight = document.getElementById('kpi-weight');
    if (kpiWeight) kpiWeight.innerText = kpis.total_weight_kg + " kg";
}

export function updateLastUpdatedTime(startIso, endIso) {
    const s = dateTimeFmt.format(new Date(startIso));
    const e = dateTimeFmt.format(new Date(endIso));
    document.getElementById('last-update').innerText = `Datos: ${s} al ${e}`;
}

export function renderSummaryTable(products) {
    const tbody = document.getElementById('summary-table-body');
    tbody.innerHTML = '';
    products.sort((a,b) => b.cantidad - a.cantidad);
    
    products.forEach(p => {
        const name = p.product_name.replace(/_/g, ' ');
        // Agregamos el círculo de color ANTES del nombre
        const row = `
            <tr>
                <td>
                    <span style="display:inline-block; width:12px; height:12px; background-color:${p.color}; border-radius:50%; margin-right:8px; border:1px solid #ccc;"></span>
                    ${name}
                </td>
                <td class="text-end fw-bold">${p.cantidad.toLocaleString()}</td>
                <td class="text-end text-muted">${p.percent}%</td>
            </tr>
        `;
        tbody.innerHTML += row;
    });
}

export function renderDowntimeTable(events) {
    const tbody = document.getElementById('downtime-table-body');
    tbody.innerHTML = '';
    if (!events.length) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">Sin paradas</td></tr>';
        return;
    }
    events.forEach(evt => {
        const dur = evt.duration_formatted.replace('0 days ', '').split('.')[0];
        const start = dateTimeFmt.format(new Date(evt.start_time));
        const end = timeFmt.format(new Date(evt.end_time));
        const row = `<tr><td><span class="badge bg-dark">${evt.line}</span></td><td>${start}</td><td>${end}</td><td class="text-danger fw-bold">${dur}</td></tr>`;
        tbody.innerHTML += row;
    });
}

export function showLoading(isLoading) {
    document.body.style.cursor = isLoading ? 'wait' : 'default';
    const btn = document.getElementById('btn-filter');
    if(btn) btn.disabled = isLoading;
}