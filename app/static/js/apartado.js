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
    
    // Abrir modal
    botonAbrir.addEventListener('click', () => {
        modal.style.display = 'block';
    });

    // Cerrar modal
    botonCerrar.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    // Buscar productos al escribir
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
        const monto = document.getElementById('monto-inicial').value;

        const datos = {
            nombre,
            apellido,
            telefono,
            id_producto: idProducto,
            monto
        };

        fetch('/api/crear_apartado', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(datos)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Apartado guardado exitosamente');
                modal.style.display = 'none';
            } else {
                alert('Error al guardar el apartado');
            }
        })
        .catch(error => {
            console.error('Error al guardar apartado:', error);
            alert('Error al guardar apartado');
        });
    });
});
