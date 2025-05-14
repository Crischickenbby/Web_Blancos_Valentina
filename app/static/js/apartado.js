document.addEventListener('DOMContentLoaded', () => {
    // Elementos del DOM
    const inputBusqueda = document.getElementById('buscador-producto');
    const tablaProductos = document.getElementById('tabla-productos');
    const cuerpoTabla = document.getElementById('cuerpo-tabla-productos');
    const idProducto = document.getElementById('id-producto');
    const productoSeleccionado = document.getElementById('producto-seleccionado');
    const modal = document.getElementById('modal-apartado');
    const botonAbrir = document.getElementById('nuevo-apartado');
    const botonCerrar = document.getElementById('cerrar-modal');
    const formApartado = document.getElementById('form-apartado');
    const modalAcciones = document.getElementById('modal-acciones-apartado');
    const infoApartado = document.getElementById('info-apartado');
    const cerrarModalAcciones = document.getElementById('cerrar-modal-acciones');
    const buscadorApartados = document.getElementById('buscador-apartado');
    const listaApartados = document.getElementById('lista-apartados');
    
    let currentApartado = null;

    // Abrir modal nuevo apartado
    botonAbrir.addEventListener('click', () => {
        modal.style.display = 'block';
        formApartado.reset();
        productoSeleccionado.textContent = '';
        idProducto.value = '';
    });

    // Cerrar modal nuevo apartado
    botonCerrar.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    // Cerrar modal de acciones
    cerrarModalAcciones.addEventListener('click', () => {
        modalAcciones.style.display = 'none';
    });

    // Cerrar modales al hacer clic fuera
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
        if (e.target === modalAcciones) {
            modalAcciones.style.display = 'none';
        }
    });

    // Buscar productos para apartado
    inputBusqueda.addEventListener('input', debounce(() => {
        const query = inputBusqueda.value.trim();
        if (query.length === 0) {
            tablaProductos.style.display = 'none';
            cuerpoTabla.innerHTML = '';
            return;
        }

        fetch(`/api/buscar_productos?q=${encodeURIComponent(query)}`)
            .then(res => {
                if (!res.ok) throw new Error('Error en la búsqueda');
                return res.json();
            })
            .then(data => {
                cuerpoTabla.innerHTML = '';
                if (data.length > 0) {
                    tablaProductos.style.display = 'block';
                    data.forEach(producto => {
                        const fila = document.createElement('tr');
                        fila.innerHTML = `
                            <td>${producto.nombre}</td>
                            <td>${producto.descripcion || '-'}</td>
                            <td>${producto.categoria || '-'}</td>
                        `;
                        fila.addEventListener('click', () => {
                            productoSeleccionado.textContent = `Seleccionado: ${producto.nombre}`;
                            idProducto.value = producto.id;
                            tablaProductos.style.display = 'none';
                        });
                        cuerpoTabla.appendChild(fila);
                    });
                } else {
                    tablaProductos.style.display = 'none';
                }
            })
            .catch(err => {
                console.error('Error al buscar productos:', err);
                alert('Error al buscar productos');
            });
    }, 300));

    // Buscar apartados por nombre/apellido
    buscadorApartados.addEventListener('input', debounce(() => {
        const query = buscadorApartados.value.trim().toLowerCase();
        const cards = listaApartados.querySelectorAll('.apartado-card');
        
        cards.forEach(card => {
            const nombreCompleto = card.dataset.nombre.toLowerCase();
            if (nombreCompleto.includes(query)) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    }, 300));

    // Guardar nuevo apartado
    formApartado.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const nombre = document.getElementById('nombre-cliente').value.trim();
        const apellido = document.getElementById('apellido-cliente').value.trim();
        const telefono = document.getElementById('telefono-cliente').value.trim();
        const productoId = idProducto.value;
        const montoInicial = parseFloat(document.getElementById('monto-inicial').value);
        const metodoPago = document.getElementById('metodo-pago').value;

        // Validaciones
        if (!nombre || !apellido || !telefono) {
            alert('Por favor complete todos los campos del cliente');
            return;
        }

        if (!productoId) {
            alert('Debe seleccionar un producto');
            return;
        }

        if (isNaN(montoInicial) || montoInicial <= 0) {
            alert('Ingrese un monto válido');
            return;
        }

        const datos = { 
            nombre, 
            apellido, 
            telefono, 
            id_producto: productoId, 
            abono_inicial: montoInicial.toFixed(2),
            metodo_pago: metodoPago
        };

        try {
            const response = await fetch('/api/crear_apartado', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(datos)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Error al guardar el apartado');
            }

            if (data.success) {
                alert('Apartado guardado exitosamente');
                modal.style.display = 'none';
                location.reload();
            } else {
                alert(data.message || 'Error al guardar el apartado');
            }
        } catch (error) {
            console.error('Error:', error);
            alert(`Error: ${error.message}`);
        }
    });

    // Manejar clics en tarjetas de apartado
    listaApartados.addEventListener('click', (e) => {
        const card = e.target.closest('.apartado-card');
        if (!card) return;

        const nombre = card.dataset.nombre;
        const id = card.dataset.id;
        const fecha = card.querySelector('p:nth-of-type(1)').textContent;
        const vence = card.querySelector('p:nth-of-type(2)').textContent;
        const producto = card.querySelector('p:nth-of-type(3)').textContent;
        const pendienteTexto = card.querySelector('p:nth-of-type(4)').textContent;
        const pendiente = parseFloat(pendienteTexto.replace(/[^\d.]/g, ''));

        currentApartado = {
            id, nombre, fecha, vence, producto, pendiente
        };

        infoApartado.innerHTML = `
            <p><strong>Cliente:</strong> ${nombre}</p>
            <p><strong>Fecha:</strong> ${fecha}</p>
            <p><strong>Vence:</strong> ${vence}</p>
            <p><strong>Producto:</strong> ${producto}</p>
            <p><strong>Pendiente:</strong> $${pendiente.toFixed(2)}</p>
        `;

        document.getElementById('monto-pago').value = '';
        modalAcciones.style.display = 'block';
    });

    // Pagar parcialmente
    document.getElementById('btn-pagar-parcial').addEventListener('click', async () => {
        const monto = parseFloat(document.getElementById('monto-pago').value);
        const metodoPago = document.getElementById('metodo-pago-pago').value;

        if (!currentApartado) return;

        if (isNaN(monto) ){
            alert('Ingrese un monto válido');
            return;
        }

        if (monto <= 0) {
            alert('El monto debe ser mayor a cero');
            return;
        }

        if (monto > currentApartado.pendiente) {
            alert('No puede pagar más del monto pendiente');
            return;
        }

        try {
            const response = await fetch('/api/realizar_pago', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    id_layaway: currentApartado.id, 
                    monto: monto.toFixed(2),
                    metodo_pago: metodoPago
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Error al realizar el pago');
            }

            if (data.success) {
                alert('Pago realizado exitosamente');
                location.reload();
            } else {
                alert(data.message || 'Error al realizar el pago');
            }
        } catch (error) {
            console.error('Error al realizar el pago:', error);
            alert(`Error: ${error.message}`);
        }
    });

    // Pagar todo
    document.getElementById('btn-pagar-todo').addEventListener('click', async () => {
        if (!currentApartado) return;

        const confirmacion = confirm(`¿Está seguro que desea pagar el total pendiente de $${currentApartado.pendiente.toFixed(2)}?`);
        if (!confirmacion) return;

        const metodoPago = document.getElementById('metodo-pago-pago').value;

        try {
            const response = await fetch('/api/realizar_pago', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    id_layaway: currentApartado.id, 
                    monto: currentApartado.pendiente.toFixed(2),
                    metodo_pago: metodoPago
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Error al realizar el pago completo');
            }

            if (data.success) {
                alert('Pago completo realizado exitosamente');
                location.reload();
            } else {
                alert(data.message || 'Error al realizar el pago completo');
            }
        } catch (error) {
            console.error('Error al pagar todo:', error);
            alert(`Error: ${error.message}`);
        }
    });

    // Cancelar apartado
    document.getElementById('btn-cancelar-apartado').addEventListener('click', async () => {
        if (!currentApartado) return;

        const confirmacion = confirm('¿Está seguro que desea cancelar este apartado?');
        if (!confirmacion) return;

        try {
            const response = await fetch('/api/cancelar_apartado', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id_layaway: currentApartado.id })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Error al cancelar el apartado');
            }

            if (data.success) {
                alert('Apartado cancelado correctamente');
                location.reload();
            } else {
                alert(data.message || 'Error al cancelar el apartado');
            }
        } catch (error) {
            console.error('Error al cancelar apartado:', error);
            alert(`Error: ${error.message}`);
        }
    });

    // Función debounce para mejor performance en búsquedas
    function debounce(func, wait) {
        let timeout;
        return function() {
            const context = this, args = arguments;
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                func.apply(context, args);
            }, wait);
        };
    }
});