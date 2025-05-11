document.addEventListener('DOMContentLoaded', () => {
    const inputBusqueda = document.getElementById('buscador-producto');
    const tablaProductos = document.getElementById('tabla-productos');
    const cuerpoTabla = document.getElementById('cuerpo-tabla-productos');
    const idProducto = document.getElementById('id-producto');
    const productoSeleccionado = document.getElementById('producto-seleccionado');
    const modal = document.getElementById('modal-apartado');
    const botonAbrir = document.getElementById('nuevo-apartado');
    const botonCerrar = document.getElementById('cerrar-modal');

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
});
