document.addEventListener('DOMContentLoaded', function () {
    const btnBuscarVenta = document.getElementById('btn-buscar-venta');
    const buscarVentaInput = document.getElementById('buscar-venta');
    const infoVentaDiv = document.getElementById('info-venta');
    const ventaIdSpan = document.getElementById('venta-id');
    const ventaFechaSpan = document.getElementById('venta-fecha');
    const ventaTotalSpan = document.getElementById('venta-total');
    const tablaProductosVenta = document.getElementById('tabla-productos-venta');
    const confirmarDevolucionBtn = document.getElementById('confirmar-devolucion');
    const reintegrarStockSelect = document.getElementById('reintegrar-stock');
    const metodoReembolsoSelect = document.getElementById('metodo-reembolso');
    const mensajeDevolucion = document.getElementById('mensaje-devolucion');
    const observacionesInput = document.getElementById('observaciones');

    const modal = document.getElementById('modal-devolucion');
    const modalContent = document.getElementById('detalle-devolucion-content');
    const cerrarModal = document.getElementById('cerrar-modal');

    let ventaActual = null;

    const tipoBusquedaSelect = document.getElementById('tipo-busqueda');
    const buscarFechaInput = document.getElementById('buscar-fecha');

    // Cambiar entre los campos según la selección
    tipoBusquedaSelect.addEventListener('change', function () {
        if (this.value === 'id') {
            buscarVentaInput.style.display = 'block';
            buscarFechaInput.style.display = 'none';
        } else if (this.value === 'fecha') {
            buscarVentaInput.style.display = 'none';
            buscarFechaInput.style.display = 'block';
        }
    });

    // Inicializar el estado (por defecto: buscar por ID)
    buscarVentaInput.style.display = 'block';
    buscarFechaInput.style.display = 'none';

    btnBuscarVenta.addEventListener('click', async function () {
        const tipoBusqueda = document.getElementById('tipo-busqueda').value;
        const buscar = buscarVentaInput.value.trim();
        const fecha = document.getElementById('buscar-fecha').value;

        if (tipoBusqueda === 'id' && buscar === '') {
            alert('Ingresa un ID de venta.');
            return;
        }

        if (tipoBusqueda === 'fecha' && fecha === '') {
            alert('Selecciona una fecha.');
            return;
        }

        try {
            const url = tipoBusqueda === 'id'
                ? `/api/buscar_venta?buscar=${encodeURIComponent(buscar)}`
                : `/api/buscar_venta?fecha=${encodeURIComponent(fecha)}`;

            const response = await fetch(url);
            const data = await response.json();

            if (data.success) {
                if (tipoBusqueda === 'id') {
                    mostrarVenta(data.venta);
                    ventaActual = data.venta;
                } else if (tipoBusqueda === 'fecha') {
                    mostrarVentasPorFecha(data.ventas);
                }
            } else {
                alert(data.message || 'No se encontraron resultados.');
            }
        } catch (error) {
            console.error('Error al buscar venta:', error);
            alert('Ocurrió un error al buscar la venta.');
        }
    });

    function mostrarVentasPorFecha(ventas) {
        const modalContent = document.getElementById('detalle-devolucion-content');
        modalContent.innerHTML = `
            <h3>Ventas encontradas:</h3>
            <ul>
                ${ventas.map(v => `
                    <li>
                        <button class="btn-seleccionar-venta" data-id="${v.id_sale}">
                            Venta ID: ${v.id_sale} - Total: $${v.total_amount.toFixed(2)} - Fecha: ${v.date}
                        </button>
                    </li>
                `).join('')}
            </ul>
        `;
        modal.style.display = 'block';

        document.querySelectorAll('.btn-seleccionar-venta').forEach(btn => {
            btn.addEventListener('click', async function () {
                const idVenta = this.getAttribute('data-id');
                modal.style.display = 'none';
                const response = await fetch(`/api/buscar_venta?buscar=${encodeURIComponent(idVenta)}`);
                const data = await response.json();
                if (data.success) {
                    mostrarVenta(data.venta);
                    ventaActual = data.venta;
                } else {
                    alert('Error al cargar la venta seleccionada.');
                }
            });
        });
    }

    function mostrarVenta(venta) {
        infoVentaDiv.style.display = 'block';
        ventaIdSpan.textContent = venta.id_sale;
        ventaFechaSpan.textContent = venta.date;
        ventaTotalSpan.textContent = `$${parseFloat(venta.total_amount).toFixed(2)}`;

        tablaProductosVenta.innerHTML = '';

        // Mostrar mensaje si ya tiene devoluciones
        if (venta.devoluciones && venta.devoluciones.length > 0) {
            mensajeDevolucion.innerHTML = `
                <p style="color: red; font-weight: bold;">
                    Esta venta ya tiene devoluciones registradas.
                </p>
                <button id="ver-devoluciones" class="btn-ver-devoluciones">Ver devoluciones</button>
            `;

            // Agregar evento al botón para mostrar detalles de devoluciones
            document.getElementById('ver-devoluciones').addEventListener('click', () => {
                mostrarDetallesModal(venta.devoluciones);
            });
        } else {
            mensajeDevolucion.innerHTML = '';
        }

        venta.productos.forEach(producto => {
            // Calcular la cantidad ya devuelta
            const cantidadDevuelta = venta.devoluciones
                ? venta.devoluciones.reduce((sum, devolucion) => {
                      const detalle = devolucion.productos.find(p => p.id === producto.id);
                      return sum + (detalle ? detalle.quantity : 0);
                  }, 0)
                : 0;

            const cantidadDisponible = producto.quantity - cantidadDevuelta;

            const fila = document.createElement('tr');
            fila.innerHTML = `
                <td>${producto.name}</td>
                <td>${producto.quantity}</td>
                <td>${producto.precio !== undefined && producto.precio !== null ? `$${parseFloat(producto.precio).toFixed(2)}` : 'N/A'}</td>
                <td><input type="checkbox" class="producto-devolver" ${cantidadDisponible <= 0 ? 'disabled' : ''}></td>
                <td><input type="number" class="cantidad-devolver" min="1" max="${cantidadDisponible}" value="0" disabled></td>
            `;
            tablaProductosVenta.appendChild(fila);
        });

        const checkboxes = tablaProductosVenta.querySelectorAll('.producto-devolver');
        const cantidades = tablaProductosVenta.querySelectorAll('.cantidad-devolver');

        checkboxes.forEach((checkbox, i) => {
            checkbox.addEventListener('change', () => {
                cantidades[i].disabled = !checkbox.checked;
                if (!checkbox.checked) cantidades[i].value = 0;
            });
        });

        cantidades.forEach((input, i) => {
            input.addEventListener('input', function () {
                const max = parseInt(input.max);
                const val = parseInt(this.value);
                if (val < 1) {
                    this.value = 1;
                } else if (val > max) {
                    this.value = max;
                }
            });
        });
    }

    confirmarDevolucionBtn.addEventListener('click', async function () {
        if (!ventaActual) {
            alert('Primero busca una venta.');
            return;
        }

        const productosADevolver = [];
        const checkboxes = tablaProductosVenta.querySelectorAll('.producto-devolver');
        const cantidades = tablaProductosVenta.querySelectorAll('.cantidad-devolver');

        checkboxes.forEach((checkbox, index) => {
            if (checkbox.checked) {
                const cantidad = parseInt(cantidades[index].value);
                if (cantidad > 0) {
                    productosADevolver.push({
                        id_producto: ventaActual.productos[index].id,
                        cantidad: cantidad,
                        precio: ventaActual.productos[index].precio
                    });
                }
            }
        });

        if (productosADevolver.length === 0) {
            alert('Selecciona al menos un producto y una cantidad válida para devolver.');
            return;
        }

        const reintegrarStock = parseInt(reintegrarStockSelect.value);
        const metodoReembolso = parseInt(metodoReembolsoSelect.value);
        const observaciones = observacionesInput.value.trim();

        const datos = {
            id_venta: ventaActual.id_sale,
            productos: productosADevolver,
            reintegrar_stock: reintegrarStock,
            metodo_reembolso: metodoReembolso,
            observaciones: observaciones
        };

        try {
            const response = await fetch('/api/registrar_devolucion', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(datos)
            });

            const data = await response.json();
            if (data.success) {
                alert('Devolución registrada correctamente.');
                location.reload();
            } else {
                alert(data.message || 'Ocurrió un error al registrar la devolución.');
            }
        } catch (error) {
            console.error('Error al registrar devolución:', error);
            alert('Ocurrió un error al registrar la devolución.');
        }
    });

    cerrarModal.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    function mostrarDetallesModal(devoluciones) {
        modalContent.innerHTML = devoluciones.map(devolucion => `
            <div class="detalle-devolucion">
                <p><strong>ID Devolución:</strong> ${devolucion.id_return}</p>
                <p><strong>Fecha:</strong> ${devolucion.date_return}</p>
                <p><strong>Método:</strong> ${devolucion.payment_method === 1 ? 'Efectivo' : 'Otro'}</p>
                <p><strong>Observaciones:</strong> ${devolucion.observations || 'Ninguna'}</p>
                <p><strong>Dinero total devuelto:</strong> $${parseFloat(devolucion.total_refund).toFixed(2)}</p>
                <h3>Productos devueltos:</h3>
                <ul>
                    ${devolucion.productos.map(p => `<li>${p.name} - ${p.quantity} unidades</li>`).join('')}
                </ul>
            </div>
        `).join('');
        modal.style.display = 'block';
    }
});
