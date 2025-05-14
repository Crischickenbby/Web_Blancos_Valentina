document.addEventListener('DOMContentLoaded', function() {
    const elementos = {
        estado: document.getElementById('estado-caja'),
        seccionAbrir: document.getElementById('seccion-abrir'),
        seccionCerrar: document.getElementById('seccion-cerrar'),
        btnAbrir: document.getElementById('btn-abrir-caja'),
        montoInicial: document.getElementById('monto-inicial'),
        fechaApertura: document.getElementById('fecha-apertura')  // <- agregado
    };

    let estadoCaja = {
        abierta: false,
        id: null,
        apertura: null
    };

    init();

    async function init() {
        await verificarEstadoCaja();
        setupEventListeners();
    }

    function setupEventListeners() {
        if (elementos.btnAbrir) {
            elementos.btnAbrir.addEventListener('click', abrirCaja);
        }
    }

    async function verificarEstadoCaja() {
        try {
            elementos.estado.innerHTML = '<i class="fas fa-sync-alt fa-spin"></i> Verificando estado...';
            elementos.estado.className = 'alert alert-info';

            const response = await fetch('/api/caja/estado');
            const data = await response.json();

            if (data.abierta) {
                estadoCaja = {
                    abierta: true,
                    id: data.id_cash_cut,
                    apertura: new Date(data.fecha_apertura)
                };

                const fechaFormateada = estadoCaja.apertura.toLocaleString();

                elementos.estado.innerHTML = `
                    <i class="fas fa-check-circle"></i> Caja abierta desde: ${fechaFormateada}
                `;
                elementos.estado.className = 'alert alert-success';

                // Mostrar fecha de apertura también en la sección de corte
                if (elementos.fechaApertura) {
                    elementos.fechaApertura.textContent = fechaFormateada;
                }

                elementos.seccionAbrir.style.display = 'none';
                if (elementos.seccionCerrar) {
                    elementos.seccionCerrar.style.display = 'block';
                }
            } else {
                estadoCaja = { abierta: false, id: null, apertura: null };
                elementos.estado.innerHTML = '<i class="fas fa-times-circle"></i> Caja cerrada';
                elementos.estado.className = 'alert alert-danger';
                elementos.seccionAbrir.style.display = 'block';
                if (elementos.seccionCerrar) {
                    elementos.seccionCerrar.style.display = 'none';
                }
            }
        } catch (error) {
            console.error('Error:', error);
            elementos.estado.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Error al verificar estado';
            elementos.estado.className = 'alert alert-warning';
        }
    }

    async function abrirCaja() {
        const monto = parseFloat(elementos.montoInicial.value) || 0;

        if (!monto || isNaN(monto)) {
            alert('Ingrese un monto válido');
            return;
        }

        try {
            elementos.btnAbrir.disabled = true;
            elementos.btnAbrir.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';

            const response = await fetch('/api/caja/abrir', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ monto: monto })

            });

            const result = await response.json();

            if (result.success) {
                await verificarEstadoCaja();
                elementos.montoInicial.value = '';
            } else {
                alert(result.message || 'Error al abrir caja');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error al abrir caja');
        } finally {
            elementos.btnAbrir.disabled = false;
            elementos.btnAbrir.innerHTML = '<i class="fas fa-lock-open"></i> Abrir Caja';
        }
    }
});
