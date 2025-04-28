document.addEventListener('DOMContentLoaded', function () {
  // =================== MODAL ELIMINAR PRODUCTO ===================
  const deleteModal = document.getElementById('deleteProductModal');
  const deleteBtn = document.querySelector('.custom-button2');
  const closeDeleteBtn = deleteModal.querySelector('.close-button');
  const deleteSelectedProductBtn = document.getElementById('deleteSelectedProduct');
  const productList = document.getElementById('productList');

  deleteBtn.addEventListener('click', () => deleteModal.style.display = 'block');
  closeDeleteBtn.addEventListener('click', () => deleteModal.style.display = 'none');
  window.addEventListener('click', e => { if (e.target === deleteModal) deleteModal.style.display = 'none'; });

  productList.addEventListener('click', function (e) {
    productList.querySelectorAll('li').forEach(item => item.classList.remove('selected'));
    if (e.target.tagName === 'LI') e.target.classList.add('selected');
  });

  deleteSelectedProductBtn.addEventListener('click', () => {
    const selectedProduct = productList.querySelector('li.selected');
    if (!selectedProduct) return alert('Por favor, selecciona un producto para eliminar.');
    
    const productId = selectedProduct.getAttribute('data-product-id');
    fetch(`/eliminar_producto/${productId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' }
    })
      .then(res => res.ok ? res.json() : Promise.reject('Error del servidor'))
      .then(data => {
        if (data.success) {
          alert('Producto eliminado correctamente');
          selectedProduct.remove();
          deleteModal.style.display = 'none';
          location.reload();
        } else alert('Error: ' + data.message);
      })
      .catch(err => {
        console.error('Error:', err);
        alert('Ocurrió un error al eliminar el producto');
      });
  });



  // =================== FILTRO ===================
  document.getElementById('searchProduct').addEventListener('input', function () {
    const filter = this.value.toLowerCase();
    productList.querySelectorAll('li').forEach(item => {
      item.style.display = item.textContent.toLowerCase().includes(filter) ? '' : 'none';
    });
  });

  document.getElementById('searchTable').addEventListener('input', function () {
    const filter = this.value.toLowerCase();
    document.querySelectorAll('.table-widget tbody tr').forEach(row => {
      const rowText = Array.from(row.querySelectorAll('td')).map(td => td.textContent.toLowerCase()).join(' ');
      row.style.display = rowText.includes(filter) ? '' : 'none';
    });
  });

  // =================== MODAL AÑADIR PRODUCTO ===================
  const addProductModal = document.getElementById('addProductModal');
  document.getElementById('addProductBtn').addEventListener('click', () => addProductModal.style.display = 'block');
  addProductModal.querySelector('.close-button').addEventListener('click', () => addProductModal.style.display = 'none');
  window.addEventListener('click', e => { if (e.target === addProductModal) addProductModal.style.display = 'none'; });

  document.getElementById('addProductForm').addEventListener('submit', function (e) {
    e.preventDefault();
    const formData = new FormData(this);

    fetch('/agregar_producto', { method: 'POST', body: formData })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          alert('Producto guardado correctamente');
          addProductModal.style.display = 'none';
          location.reload();
        } else alert('Error: ' + data.message);
      })
      .catch(err => {
        console.error('Error:', err);
        alert('Ocurrió un error al guardar el producto');
      });
  });

  // =================== MODAL AÑADIR CANTIDAD ===================
  const quantityModal = document.getElementById('addQuantityModal');
  const quantityForm = document.getElementById('addQuantityForm');
  let currentProductId = null;

  // Agregar evento a los botones de "Añadir Cantidad"
  document.querySelectorAll('.add-quantity-btn').forEach(button => {
    button.addEventListener('click', function () {
      currentProductId = this.getAttribute('data-id');
      console.log("ID del producto seleccionado:", currentProductId); // Verificar el ID del producto
      quantityModal.style.display = 'block';
    });
  });

  // Cerrar el modal al hacer clic en el botón de cerrar
  quantityModal.querySelector('.close-button').addEventListener('click', () => {
    console.log("Modal de añadir cantidad cerrado."); // Confirmar cierre del modal
    quantityModal.style.display = 'none';
  });

  // Cerrar el modal al hacer clic fuera de él
  window.addEventListener('click', e => {
    if (e.target === quantityModal) {
      console.log("Clic fuera del modal, cerrando."); // Confirmar cierre por clic fuera
      quantityModal.style.display = 'none';
    }
  });

  // Manejar el envío del formulario
  quantityForm.addEventListener('submit', function (e) {
    e.preventDefault();
    const quantity = document.getElementById('quantityToAdd').value;
    console.log("Cantidad ingresada:", quantity); // Verificar la cantidad ingresada

    fetch('/incrementar_cantidad_producto', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ product_id: currentProductId, quantity_to_add: quantity })
    })
      .then(res => {
        console.log("Respuesta del servidor:", res); // Verificar la respuesta del servidor
        return res.json();
      })
      .then(data => {
        console.log("Datos recibidos del servidor:", data); // Verificar los datos recibidos
        if (data.success) {
          alert('Cantidad añadida correctamente');
          quantityModal.style.display = 'none';
          location.reload();
        } else {
          alert('Error: ' + data.message);
        }
      })
      .catch(err => {
        console.error("Error al realizar la solicitud:", err); // Verificar errores en la solicitud
        alert('Ocurrió un error al añadir la cantidad');
      });
  });

  // =================== MODAL ELIMINAR CANTIDAD ===================
  const removeQuantityModal = document.getElementById('removeQuantityModal');
  const removeQuantityForm = document.getElementById('removeQuantityForm');
  let currentProductStock = null;

  // Agregar evento a los botones de "Eliminar Cantidad"
  document.querySelectorAll('.delete-product-btn').forEach(button => {
    button.addEventListener('click', function () {
      currentProductId = this.getAttribute('data-id');
      currentProductStock = parseInt(this.closest('tr').querySelector('td:nth-child(3)').textContent); // Obtener la cantidad en existencia
      console.log("ID del producto seleccionado:", currentProductId); // Depuración
      console.log("Cantidad en existencia:", currentProductStock); // Depuración
      removeQuantityModal.style.display = 'block';
    });
  });

  // Cerrar el modal al hacer clic en el botón de cerrar
  removeQuantityModal.querySelector('.close-button').addEventListener('click', () => {
    console.log("Modal de eliminar cantidad cerrado."); // Confirmar cierre del modal
    removeQuantityModal.style.display = 'none';
  });

  // Cerrar el modal al hacer clic fuera de él
  window.addEventListener('click', e => {
    if (e.target === removeQuantityModal) {
      console.log("Clic fuera del modal, cerrando."); // Confirmar cierre por clic fuera
      removeQuantityModal.style.display = 'none';
    }
  });

  // Manejar el envío del formulario
  removeQuantityForm.addEventListener('submit', function (e) {
    e.preventDefault();
    const quantityToRemove = parseInt(document.getElementById('quantityToRemove').value);
    console.log("Cantidad a eliminar ingresada:", quantityToRemove); // Verificar la cantidad ingresada

    // Validar que la cantidad a eliminar sea válida
    if (quantityToRemove < 1 || quantityToRemove > currentProductStock) {
      alert(`La cantidad a eliminar debe estar entre 1 y ${currentProductStock}.`);
      return;
    }

    fetch(`/reducir_cantidad_producto`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ product_id: currentProductId, quantity_to_remove: quantityToRemove })
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        alert('Cantidad eliminada correctamente');
        location.reload();
      } else {
        alert('Error: ' + data.message);
      }
    })
    .catch(err => {
      console.error("Error al realizar la solicitud:", err);
      alert('Ocurrió un error al eliminar la cantidad');
    });
  });

  // =================== MODAL EDITAR PRODUCTO ===================
  const editProductModal = document.getElementById('editProductModal');
  const editProductForm = document.getElementById('editProductForm');
  
  // Agregar evento a los botones de "Editar"
  document.querySelectorAll('.edit-product-btn').forEach(button => {
    button.addEventListener('click', function () {
      currentProductId = this.getAttribute('data-id');
      console.log("ID del producto a editar:", currentProductId); // Verificar el ID del producto
      
      // Obtener los datos del producto de la fila correspondiente
      const row = this.closest('tr');
      const name = row.cells[0].textContent;
      const description = row.cells[1].textContent;
      const price = parseFloat(row.cells[3].textContent.replace('$', ''));
      const category = row.cells[4].textContent;
      
      console.log("Datos obtenidos:", { name, description, price, category }); // Verificar datos obtenidos
      
      // Rellenar el formulario con los datos actuales
      document.getElementById('edit-product-name').value = name;
      document.getElementById('edit-product-description').value = description;
      document.getElementById('edit-product-price').value = price;
      
      // Seleccionar la categoría correcta
      const categorySelect = document.getElementById('edit-category-select');
      for (let i = 0; i < categorySelect.options.length; i++) {
        if (categorySelect.options[i].textContent === category) {
          categorySelect.selectedIndex = i;
          break;
        }
      }
      
      // Mostrar el modal
      editProductModal.style.display = 'block';
    });
  });
  
  // Cerrar el modal al hacer clic en el botón de cerrar
  editProductModal.querySelector('.close-button').addEventListener('click', () => {
    console.log("Modal de edición cerrado."); // Confirmar cierre del modal
    editProductModal.style.display = 'none';
  });
  
  // Cerrar el modal al hacer clic fuera de él
  window.addEventListener('click', e => {
    if (e.target === editProductModal) {
      console.log("Clic fuera del modal de edición, cerrando."); // Confirmar cierre por clic fuera
      editProductModal.style.display = 'none';
    }
  });
  
  // Manejar el envío del formulario de edición
  editProductForm.addEventListener('submit', function (e) {
    e.preventDefault();
    
    // Obtener los valores del formulario
    const productName = document.getElementById('edit-product-name').value;
    const productDescription = document.getElementById('edit-product-description').value;
    const productPrice = document.getElementById('edit-product-price').value;
    const productCategory = document.getElementById('edit-category-select').value;
    
    console.log("Datos a enviar:", { productName, productDescription, productPrice, productCategory }); // Verificar datos
    
    // Crear objeto con los datos a enviar
    const data = {
      product_id: currentProductId,
      name: productName,
      description: productDescription,
      price: productPrice,
      category_id: productCategory
    };
    
    // Enviar datos al servidor mediante fetch
    fetch('/actualizar_producto', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data)
    })
    .then(res => {
      console.log("Respuesta del servidor:", res); // Verificar la respuesta del servidor
      return res.json();
    })
    .then(data => {
      if (data.success) {
        alert('Producto actualizado correctamente');
        editProductModal.style.display = 'none';
        location.reload();
      } else {
        alert('Error: ' + data.message);
      }
    })
    .catch(err => {
      console.error("Error al realizar la solicitud:", err);
      alert('Ocurrió un error al actualizar el producto');
    });
  });
});




// JavaScript para manejar el modal de categorías
document.addEventListener('DOMContentLoaded', function() {
  // Elementos del modal de categorías
  const manageCategoriesBtn = document.getElementById('manageCategoriesBtn');
  const manageCategoriesModal = document.getElementById('manageCategoriesModal');
  const addCategoryForm = document.getElementById('addCategoryForm');
  const categoryList = document.getElementById('categoryList');

  // Abrir modal de categorías
  manageCategoriesBtn.addEventListener('click', function() {
      manageCategoriesModal.style.display = "block";
  });

  // Cerrar modales cuando se hace clic en el botón de cerrar
  document.querySelectorAll('.close-button').forEach(function(button) {
      button.addEventListener('click', function() {
          const modal = button.closest('.modal');
          if (modal) {
              modal.style.display = "none";
          }
      });
  });

  // Cerrar modal haciendo clic fuera del contenido
  window.addEventListener('click', function(event) {
      if (event.target.classList.contains('modal')) {
          event.target.style.display = "none";
      }
  });

  // Manejar el envío del formulario para añadir categoría
  addCategoryForm.addEventListener('submit', function (e) {
    e.preventDefault();
    const categoryName = document.getElementById('categoryName').value;

    if (categoryName.trim() !== '') {
        fetch('/add_category', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name: categoryName }),
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Categoría añadida con éxito!');
                    location.reload(); // Recargar la página después de añadir la categoría
                } else {
                    alert('Error: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error en la comunicación con el servidor');
            });
    }
});

// Manejar clic en botones de eliminar categoría
document.addEventListener('click', function (e) {
    if (e.target.closest('.delete-category-btn')) {
        const deleteButton = e.target.closest('.delete-category-btn');
        const categoryId = deleteButton.getAttribute('data-id');
        const categoryItem = deleteButton.closest('li');

        if (confirm('¿Estás seguro de que deseas eliminar esta categoría?')) {
            fetch('/delete_category', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ id: categoryId }),
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Categoría eliminada con éxito!');
                        location.reload(); // Recargar la página después de eliminar la categoría
                    } else {
                        alert('Error: ' + data.message);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Error en la comunicación con el servidor');
                });
        }
    }
});

  // Función para actualizar los select de categorías en los modales
  function updateCategorySelects(categoryId, categoryName) {
      const categorySelects = document.querySelectorAll('select[name="productCategory"]');
      categorySelects.forEach(select => {
          const option = document.createElement('option');
          option.value = categoryId;
          option.textContent = categoryName;
          select.appendChild(option);
      });
  }

  // Función para eliminar categoría de los select en los modales
  function removeCategoryFromSelects(categoryId) {
      const categorySelects = document.querySelectorAll('select[name="productCategory"]');
      categorySelects.forEach(select => {
          const optionToRemove = select.querySelector(`option[value="${categoryId}"]`);
          if (optionToRemove) {
              optionToRemove.remove();
          }
      });
  }
});