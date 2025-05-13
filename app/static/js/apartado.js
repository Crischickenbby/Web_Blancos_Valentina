document.addEventListener('DOMContentLoaded', () => {
    const inputBusqueda = document.getElementById('buscador-producto');
    const tablaProductos = document.getElementById('tabla-productos');
    const cuerpoTabla = document.getElementById('cuerpo-tabla-productos');
    const idProducto = document.getElementById('id-producto');
    const productoSeleccionado = document.getElementById('producto-seleccionado');
    const modal = document.getElementById('modal-apartado');
    const botonAbrir = document.getElementById('nuevo-apartado');
    const botonCerrar = document.getElementById('cerrar-modal');
    const botonGuardar = document.getElementById('guardar-apartado');
    const formApartado = document.getElementById('form-apartado');
    const modalAcciones = document.getElementById('modal-acciones-apartado');
    const infoApartado = document.getElementById('info-apartado');
    let currentApartado = null;

    // Abrir modal nuevo apartado
    botonAbrir.addEventListener('click', () => {
        modal.style.display = 'block';
    });

    // Cerrar modal nuevo apartado
    botonCerrar.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    // Buscar productos
    inputBusqueda.addEventListener('input', () => {
        const query = inputBusqueda.value.trim();
        if (query.length === 0) {
            tablaProductos.style.display = 'none';
            cuerpoTabla.innerHTML = '';
            return;
        }

        fetch(`/api/buscar_productos?q=${encodeURIComponent(query)}`)
            .then(res => res.json())
            .then(data => {
                cuerpoTabla.innerHTML = '';
                if (data.length > 0) {
                    tablaProductos.style.display = 'block';
                    data.forEach(producto => {
                        const fila = document.createElement('tr');
                        fila.innerHTML = `
                            <td>${producto.nombre}</td>
                            <td>${producto.descripcion}</td>
                            <td>${producto.categoria}</td>
                        `;
                        fila.addEventListener('click', () => {
                            inputBusqueda.value = '';
                            tablaProductos.style.display = 'none';
                            productoSeleccionado.textContent = `Seleccionado: ${producto.nombre}`;
                            idProducto.value = producto.id;
                        });
                        cuerpoTabla.appendChild(fila);
                    });
                } else {
                    tablaProductos.style.display = 'none';
                }
            })
            .catch(err => {
                console.error('Error al buscar productos:', err);
            });
    });

    // Cerrar modal si se hace clic fuera del contenido
    window.addEventListener('click', (e) => {
        if (e.target == modal) {
            modal.style.display = 'none';
        }
    });

    // Guardar apartado
    botonGuardar.addEventListener('click', (e) => {
        e.preventDefault();
        
        const nombre = document.getElementById('nombre-cliente').value;
        const apellido = document.getElementById('apellido-cliente').value;
        const telefono = document.getElementById('telefono-cliente').value;
        const idProducto = document.getElementById('id-producto').value;
        const abono_inicial = document.getElementById('monto-inicial').value;
        // Obtener el método de pago seleccionado
        const metodo_pago = document.getElementById("metodo-pago").value;


        const datos = { nombre, apellido, telefono, id_producto: idProducto, abono_inicial, metodo_pago };

        fetch('/api/crear_apartado', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(datos)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Apartado guardado exitosamente');
                modal.style.display = 'none';
                location.reload();
            } else {
                alert('Error al guardar el apartado');
            }
        })
        .catch(error => {
            console.error('Error al guardar apartado:', error);
            alert('Error al guardar apartado');
        });
    });

    // Escuchar clics en las tarjetas de apartado
    document.querySelectorAll('.apartado-card').forEach(card => {
        card.addEventListener('click', () => {
            const nombre = card.dataset.nombre;
            const fecha = card.querySelector('p:nth-of-type(1)').textContent;
            const vence = card.querySelector('p:nth-of-type(2)').textContent;
            const producto = card.querySelector('p:nth-of-type(3)').textContent;
            const pendienteTexto = card.querySelector('p:nth-of-type(4)').textContent;
            const pendiente = parseFloat(pendienteTexto.replace(/[^\d.]/g, ''));

            currentApartado = {
                nombre, fecha, vence, producto, pendiente,
                id: card.dataset.id
            };

            console.log("ID del apartado seleccionado:", card.dataset.id);

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
    });

// Pagar parcial
document.getElementById('btn-pagar-parcial').addEventListener('click', async () => {
    const monto = parseFloat(document.getElementById('monto-pago').value);
    const metodoPago = document.getElementById("metodo-pago-pago").value; // Obtener el método de pago

    if (!monto || monto <= 0) {
        alert('Ingresa un monto válido.');
        return;
    }

    if (monto > currentApartado.pendiente) {
        alert('No puedes pagar más del monto pendiente.');
        return;
    }

    try {
        const response = await fetch('/api/realizar_pago', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                id_layaway: currentApartado.id, 
                monto, 
                metodo_pago: metodoPago  // Incluir el método de pago en la solicitud
            })
        });

        const data = await response.json();

        if (data.success) {
            alert('Pago realizado exitosamente.');
            location.reload();
        } else {
            alert('Error al realizar el pago: ' + data.message);
        }
    } catch (error) {
        console.error('Error al realizar el pago:', error);
        alert('Error al realizar el pago');
    }
});

// Pagar todo
document.getElementById('btn-pagar-todo').addEventListener('click', async () => {
    const metodoPago = document.getElementById("metodo-pago-pago").value; // Obtener el método de pago

    try {
        const response = await fetch('/api/realizar_pago', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                id_layaway: currentApartado.id, 
                monto: currentApartado.pendiente,
                metodo_pago: metodoPago  // Incluir el método de pago en la solicitud
            })
        });

        const data = await response.json();

        if (data.success) {
            alert('Pago completo realizado.');
            location.reload();
        } else {
            alert('Error al pagar todo: ' + data.message);
        }
    } catch (error) {
        console.error('Error al pagar todo:', error);
    }
});


    // Cancelar apartado
    document.getElementById('btn-cancelar-apartado').addEventListener('click', async () => {
        if (!confirm('¿Estás seguro de que deseas cancelar este apartado?')) return;

        try {
            const response = await fetch('/api/cancelar_apartado', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id_layaway: currentApartado.id })
            });

            const data = await response.json();

            if (data.success) {
                alert('Apartado cancelado correctamente.');
                location.reload();
            } else {
                alert('Error al cancelar: ' + data.message);
            }
        } catch (error) {
            console.error('Error al cancelar apartado:', error);
        }
    });
});
