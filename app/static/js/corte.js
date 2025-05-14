document.addEventListener('DOMContentLoaded', function () {
    // Elementos del DOM
    const elementos = {
        estado: document.getElementById('estado-caja'),
        seccionAbrir: document.getElementById('seccion-abrir'),
        seccionCerrar: document.getElementById('seccion-cerrar'),
        btnAbrir: document.getElementById('btn-abrir-caja'),
        btnCerrar: document.getElementById('btn-cerrar-caja'),
        montoInicial: document.getElementById('monto-inicial'),
        efectivoContado: document.getElementById('efectivo-contado'),
        observaciones: document.getElementById('observaciones'),
        fechaApertura: document.getElementById('fecha-apertura'),
        ingresosEfectivo: document.getElementById('ingresos-efectivo'),
        egresosEfectivo: document.getElementById('egresos-efectivo'),
        totalEfectivo: document.getElementById('total-efectivo'),
        tarjetas: document.getElementById('tarjetas'),
        transferencias: document.getElementById('transferencias'),
        gananciaGeneral: document.getElementById('ganancia-general'),
        diferencia: document.getElementById('diferencia')
    };

    // Estado de la caja
    let estadoCaja = {
        abierta: false,
        id: null,
        apertura: null
    };

    // Intervalo para actualización automática
    let intervaloActualizacion;

    // Inicialización
    init();

    async function init() {
        await verificarEstadoCaja();
        setupEventListeners();
        iniciarActualizacionAutomatica();
    }

    function setupEventListeners() {
        if (elementos.btnAbrir) {
            elementos.btnAbrir.addEventListener('click', abrirCaja);
        }

        if (elementos.btnCerrar) {
            elementos.btnCerrar.addEventListener('click', cerrarCaja);
        }

        // Actualizar diferencia en tiempo real cuando cambia el efectivo contado
        if (elementos.efectivoContado) {
            elementos.efectivoContado.addEventListener('input', calcularDiferencia);
        }
    }

    function iniciarActualizacionAutomatica() {
        // Limpiar intervalo existente
        if (intervaloActualizacion) {
            clearInterval(intervaloActualizacion);
        }
        
        // Actualizar inmediatamente y luego cada 5 segundos si la caja está abierta
        if (estadoCaja.abierta) {
            actualizarDatosCorteCaja();
            intervaloActualizacion = setInterval(actualizarDatosCorteCaja, 5000);
        }
    }

    function calcularDiferencia() {
        if (!estadoCaja.abierta) return;

        const efectivoContado = parseFloat(elementos.efectivoContado.value) || 0;
        const efectivoEsperadoText = elementos.totalEfectivo.textContent.replace('$', '');
        const efectivoEsperado = parseFloat(efectivoEsperadoText) || 0;
        const diferencia = efectivoEsperado - efectivoContado;

        elementos.diferencia.textContent = `$${diferencia.toFixed(2)}`;
    }

    async function verificarEstadoCaja() {
        try {
            mostrarEstadoCaja('loading', '<i class="fas fa-sync-alt fa-spin"></i> Verificando estado...');

            const response = await fetch('/api/caja/estado');
            
            if (!response.ok) {
                throw new Error(`Error HTTP: ${response.status}`);
            }

            const data = await response.json();

            if (data.abierta) {
                estadoCaja = {
                    abierta: true,
                    id: data.id_cash_cut,
                    apertura: new Date(data.fecha_apertura)
                };

                const fechaFormateada = estadoCaja.apertura.toLocaleString();
                mostrarEstadoCaja('success', `<i class="fas fa-check-circle"></i> Caja abierta desde: ${fechaFormateada}`);

                if (elementos.fechaApertura) {
                    elementos.fechaApertura.textContent = fechaFormateada;
                }

                elementos.seccionAbrir.style.display = 'none';
                elementos.seccionCerrar.style.display = 'block';
                
                // Limpiar campos al abrir
                if (elementos.efectivoContado) elementos.efectivoContado.value = '';
                if (elementos.observaciones) elementos.observaciones.value = '';
                
                // Iniciar actualización automática
                iniciarActualizacionAutomatica();
            } else {
                estadoCaja = { abierta: false, id: null, apertura: null };
                mostrarEstadoCaja('error', '<i class="fas fa-times-circle"></i> Caja cerrada');
                elementos.seccionAbrir.style.display = 'block';
                elementos.seccionCerrar.style.display = 'none';
                
                // Detener actualización automática
                if (intervaloActualizacion) {
                    clearInterval(intervaloActualizacion);
                }
            }
        } catch (error) {
            console.error('Error al verificar estado de caja:', error);
            mostrarEstadoCaja('warning', '<i class="fas fa-exclamation-triangle"></i> Error al verificar estado');
        }
    }

    function mostrarEstadoCaja(tipo, mensaje) {
        elementos.estado.innerHTML = mensaje;
        elementos.estado.className = `alert alert-${tipo}`;
    }

    async function abrirCaja() {
        const monto = parseFloat(elementos.montoInicial.value) || 0;

        if (!monto || monto <= 0) {
            alert('Ingrese un monto válido mayor a cero');
            return;
        }

        if (!confirm(`¿Desea abrir la caja con un monto inicial de $${monto.toFixed(2)}?`)) {
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

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Error al abrir caja');
            }

            const result = await response.json();

            if (result.success) {
                await verificarEstadoCaja();
                elementos.montoInicial.value = '';
                mostrarNotificacion('success', 'Caja abierta correctamente');
            } else {
                throw new Error(result.error || result.message || 'Error al abrir caja');
            }
        } catch (error) {
            console.error('Error:', error);
            mostrarNotificacion('error', error.message);
        } finally {
            elementos.btnAbrir.disabled = false;
            elementos.btnAbrir.innerHTML = '<i class="fas fa-lock-open"></i> Abrir Caja';
        }
    }

    async function cerrarCaja() {
        const efectivoContado = parseFloat(elementos.efectivoContado.value) || 0;
        const observaciones = elementos.observaciones.value;
        
        if (!efectivoContado || efectivoContado < 0) {
            mostrarNotificacion('error', 'Ingrese un monto válido para el efectivo contado');
            return;
        }

        if (!confirm('¿Está seguro que desea cerrar la caja?')) {
            return;
        }

        try {
            elementos.btnCerrar.disabled = true;
            elementos.btnCerrar.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Cerrando caja...';

            // Calcular diferencia
            const efectivoEsperadoText = elementos.totalEfectivo.textContent.replace('$', '');
            const efectivoEsperado = parseFloat(efectivoEsperadoText) || 0;
            const diferencia = efectivoEsperado - efectivoContado;

            const response = await fetch('/api/caja/cerrar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    efectivo_contado: efectivoContado,
                    diferencia: diferencia,
                    observaciones: observaciones
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Error al cerrar caja');
            }

            const result = await response.json();

            if (result.message) {
                mostrarNotificacion('success', result.message);
                await verificarEstadoCaja();
            } else {
                throw new Error('Error al procesar el cierre de caja');
            }
        } catch (error) {
            console.error('Error:', error);
            mostrarNotificacion('error', error.message);
        } finally {
            elementos.btnCerrar.disabled = false;
            elementos.btnCerrar.innerHTML = '<i class="fas fa-lock"></i> Cerrar Caja';
        }
    }

    async function actualizarDatosCorteCaja() {
        if (!estadoCaja.abierta) return;

        try {
            const response = await fetch('/api/caja/datos-corte');
            
            if (!response.ok) return;
            
            const data = await response.json();

            if (data.success) {
                // Convertir y formatear valores
                const formatCurrency = (value) => `$${parseFloat(value || 0).toFixed(2)}`;
                
                elementos.ingresosEfectivo.textContent = formatCurrency(data.ingresos_efectivo);
                elementos.egresosEfectivo.textContent = formatCurrency(data.egresos_efectivo);
                elementos.totalEfectivo.textContent = formatCurrency(data.total_efectivo);
                elementos.tarjetas.textContent = formatCurrency(data.tarjetas);
                elementos.transferencias.textContent = formatCurrency(data.transferencias);
                elementos.gananciaGeneral.textContent = formatCurrency(data.ganancia_general);
                
                // Recalcular diferencia si hay un valor en efectivo contado
                if (elementos.efectivoContado.value) {
                    calcularDiferencia();
                }
            }
        } catch (error) {
            console.error('Error al actualizar datos de corte:', error);
        }
    }

    function mostrarNotificacion(tipo, mensaje) {
        // Puedes implementar toast notifications aquí o usar alertas simples
        alert(`[${tipo.toUpperCase()}] ${mensaje}`);
    }
});