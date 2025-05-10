document.addEventListener('DOMContentLoaded', () => {
    const buscador = document.getElementById('buscador');
    const tablaProductos = document.getElementById('tabla-productos');
    const productosSeleccionados = document.getElementById('productos-seleccionados');
    const totalVenta = document.getElementById('total-venta');
    const registrarVentaBtn = document.getElementById('registrar-venta');
    const metodoPagoSelect = document.getElementById('metodo-pago');

    let productos = [];
    let seleccionados = [];

    // Cargar productos desde el servidor
    async function cargarProductos() {
        const response = await fetch('/api/productos');
        productos = await response.json();
        renderProductos(productos);
    }

    // Renderizar productos en la tabla
    function renderProductos(productosFiltrados) {
        tablaProductos.innerHTML = '';
        productosFiltrados.forEach(producto => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${producto.nombre}</td>
                <td>${producto.descripcion}</td>
                <td>${producto.stock}</td>
                <td>$${producto.precio.toFixed(2)}</td>
                <td><button class="btn-agregar" data-id="${producto.id}">Agregar</button></td>
            `;
            tablaProductos.appendChild(row);
        });
    }

    // Filtrar productos en tiempo real
    buscador.addEventListener('input', () => {
        const filtro = buscador.value.toLowerCase();
        const productosFiltrados = productos.filter(producto =>
            producto.nombre.toLowerCase().includes(filtro)
        );
        renderProductos(productosFiltrados);
    });

    // Agregar producto al contenedor de seleccionados
    tablaProductos.addEventListener('click', (e) => {
        if (e.target.classList.contains('btn-agregar')) {
            const id = parseInt(e.target.dataset.id);
            const producto = productos.find(p => p.id === id);

            if (producto && producto.stock > 0) {
                const existente = seleccionados.find(p => p.id === id);
                if (existente) {
                    existente.cantidad++;
                } else {
                    seleccionados.push({ ...producto, cantidad: 1 });
                }
                producto.stock--;
                actualizarSeleccionados();
                renderProductos(productos);
            }
        }
    });

    // Actualizar contenedor de productos seleccionados
    function actualizarSeleccionados() {
        productosSeleccionados.innerHTML = '';
        let total = 0;

        seleccionados.forEach(producto => {
            const subtotal = producto.cantidad * producto.precio;
            total += subtotal;

            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${producto.nombre}</td>
                <td>${producto.descripcion}</td>
                <td>${producto.cantidad}</td>
                <td>$${producto.precio.toFixed(2)}</td>
                <td>$${subtotal.toFixed(2)}</td>
                <td><button class="btn-quitar" data-id="${producto.id}">Quitar</button></td>
            `;
            productosSeleccionados.appendChild(row);
        });

        totalVenta.textContent = total.toFixed(2);
    }

    // Quitar producto del contenedor de seleccionados
    productosSeleccionados.addEventListener('click', (e) => {
        if (e.target.classList.contains('btn-quitar')) {
            const id = parseInt(e.target.dataset.id);
            const index = seleccionados.findIndex(p => p.id === id);
            if (index !== -1) {
                const producto = seleccionados[index];
                productos.find(p => p.id === id).stock += producto.cantidad;
                seleccionados.splice(index, 1);
                actualizarSeleccionados();
                renderProductos(productos);
            }
        }
    });

    // Registrar venta
    registrarVentaBtn.addEventListener('click', async () => {
        if (seleccionados.length === 0) {
            alert('No puedes realizar una venta sin productos seleccionados.');
            return; // Detiene la ejecución si no hay productos seleccionados
        }

        const metodoPago = metodoPagoSelect.value;

        const venta = {
            productos: seleccionados,
            total: parseFloat(totalVenta.textContent),
            metodo_pago: parseInt(metodoPago)
        };

        console.log({
            productos: seleccionados,
            total: parseFloat(totalVenta.textContent),
            metodo_pago: parseInt(metodoPago)
        });

        const response = await fetch('/api/registrar_venta', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(venta)
        });

        if (response.ok) {
            alert('Venta registrada con éxito');
            location.reload(); // Recarga la página después de registrar la venta
        } else {
            const error = await response.json();
            alert(`Error al registrar la venta: ${error.message}`);
        }
    });

    cargarProductos();
});