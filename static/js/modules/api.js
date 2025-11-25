/**
 * Módulo encargado de la comunicación con el Backend
 */
export async function fetchDashboardData(interval, startDate = null, endDate = null) {
    try {
        // Construimos la URL con parámetros
        let url = `/api/dashboard?interval=${interval}`;
        
        if (startDate) url += `&start=${startDate}`;
        if (endDate) url += `&end=${endDate}`;

        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`Error HTTP: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error("Error en API Service:", error);
        throw error; // Re-lanzamos para que main.js maneje el error visualmente
    }
}