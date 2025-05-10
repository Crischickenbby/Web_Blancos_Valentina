// Abrir y cerrar modal
const addEmployeeBtn = document.getElementById('addEmployeeBtn');
const addEmployeeModal = document.getElementById('addEmployeeModal');
const closeButton = document.querySelector('.close-button');

addEmployeeBtn?.addEventListener('click', () => {
    addEmployeeModal.style.display = 'flex';
});

closeButton?.addEventListener('click', () => {
    addEmployeeModal.style.display = 'none';
});

window.addEventListener('click', (event) => {
    if (event.target === addEmployeeModal) {
        addEmployeeModal.style.display = 'none';
    }
});

// Abrir y cerrar el modal de edición
const editEmployeeModal = document.getElementById('editEmployeeModal');
const closeEditModal = document.getElementById('closeEditModal');

document.querySelectorAll('.custom-button2').forEach(button => {
    button.addEventListener('click', async function () {
        const userId = this.dataset.userId;
        console.log(`Obteniendo información del empleado con ID: ${userId}`); // Depuración

        try {
            const response = await fetch(`/obtener_empleado/${userId}`);
            const empleado = await response.json();

            if (empleado.success) {
                console.log('Información del empleado:', empleado); // Depuración
                // Llenar el modal con la información del empleado
                document.getElementById('editNombreEmpleado').value = empleado.data.Name;
                document.getElementById('editApellidosEmpleado').value = empleado.data.Last_Name;
                document.getElementById('editCorreoEmpleado').value = empleado.data.Email;
                document.getElementById('editContrasenaEmpleado').value = ''; // No mostrar la contraseña actual

                // Configurar los switches de privilegios
                document.getElementById('editPrivilegeVender').checked = empleado.data.Permissions.Sale;
                document.getElementById('editPrivilegeApartado').checked = empleado.data.Permissions.Layaway;
                document.getElementById('editPrivilegeCorte').checked = empleado.data.Permissions.Cash;
                document.getElementById('editPrivilegeAlmacen').checked = empleado.data.Permissions.Product;
                document.getElementById('editPrivilegeDevolucion').checked = empleado.data.Permissions.Repayment;

                // Mostrar el modal
                editEmployeeModal.style.display = 'flex';
                editEmployeeModal.dataset.userId = userId;
            } else {
                alert('Error al obtener la información del empleado.');
            }
        } catch (error) {
            console.error('Error al obtener la información del empleado:', error);
            alert('Ocurrió un error al obtener la información del empleado.');
        }
    });
});

closeEditModal.addEventListener('click', () => {
    editEmployeeModal.style.display = 'none';
});

// Manejar selección de privilegios con switches
const privilegeCheckboxes = document.querySelectorAll('.privilege-checkbox');
const privilegeInput = document.getElementById('privilegiosEmpleado');

privilegeCheckboxes.forEach(checkbox => {
    checkbox.addEventListener('change', function () {
        // Obtener todos los privilegios seleccionados
        const selectedPrivileges = Array.from(privilegeCheckboxes)
            .filter(cb => cb.checked)
            .map(cb => cb.dataset.privilege);

        // Actualizar el valor del input oculto
        privilegeInput.value = selectedPrivileges.join(',');
    });
});

// Validación de formulario
document.getElementById('crearEmpleadoForm')?.addEventListener('submit', async function (event) {
    event.preventDefault(); // Evitar el envío por defecto del formulario

    const nombre = document.getElementById('nombreEmpleado').value.trim();
    const apellidos = document.getElementById('apellidosEmpleado').value.trim();
    const correo = document.getElementById('correoEmpleado').value.trim();
    const contrasena = document.getElementById('contrasenaEmpleado').value.trim();
    const privilegios = privilegeInput?.value; // Lista separada por comas

    if (!nombre || !apellidos || !correo || !contrasena || !privilegios) {
        alert('Por favor, completa todos los campos y selecciona al menos un privilegio.');
        return;
    }

    // Enviar los datos al servidor
    try {
        const response = await fetch('/crear_empleado', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: new URLSearchParams({
                nombreEmpleado: nombre,
                apellidosEmpleado: apellidos,
                correoEmpleado: correo,
                contrasenaEmpleado: contrasena,
                privilegiosEmpleado: privilegios
            })
        });

        const result = await response.json();
        if (result.success) {
            alert(result.message);
            location.reload(); // Recargar la página para actualizar la lista de empleados
        } else {
            alert(`Error: ${result.message}`);
        }
    } catch (error) {
        console.error('Error al enviar los datos:', error);
        alert('Ocurrió un error al crear el empleado.');
    }
});

// Manejar la eliminación de empleados
document.querySelectorAll('.custom-button3').forEach(button => {
    button.addEventListener('click', async function () {
        const userId = this.dataset.userId; // Obtener el ID del usuario desde el atributo data
        const confirmDelete = confirm('¿Estás seguro de que deseas eliminar este empleado?');

        if (confirmDelete) {
            try {
                const response = await fetch(`/eliminar_empleado/${userId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                const result = await response.json();
                if (result.success) {
                    alert(result.message);
                    location.reload(); // Recargar la página para actualizar la lista de empleados
                } else {
                    alert(`Error: ${result.message}`);
                }
            } catch (error) {
                console.error('Error al eliminar el empleado:', error);
                alert('Ocurrió un error al eliminar el empleado.');
            }
        }
    });
});

// Manejar la edición de empleados
document.getElementById('editarEmpleadoForm').addEventListener('submit', async function (event) {
    event.preventDefault();

    const userId = editEmployeeModal.dataset.userId;
    const nombre = document.getElementById('editNombreEmpleado').value.trim();
    const apellidos = document.getElementById('editApellidosEmpleado').value.trim();
    const correo = document.getElementById('editCorreoEmpleado').value.trim();
    const contrasena = document.getElementById('editContrasenaEmpleado').value.trim();
    const privilegios = {
        Sale: document.getElementById('editPrivilegeVender').checked,
        Layaway: document.getElementById('editPrivilegeApartado').checked,
        Cash: document.getElementById('editPrivilegeCorte').checked,
        Product: document.getElementById('editPrivilegeAlmacen').checked,
        Repayment: document.getElementById('editPrivilegeDevolucion').checked
    };

    try {
        const response = await fetch(`/editar_empleado/${userId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                nombreEmpleado: nombre,
                apellidosEmpleado: apellidos,
                correoEmpleado: correo,
                contrasenaEmpleado: contrasena,
                privilegiosEmpleado: privilegios
            })
        });

        const result = await response.json();
        if (result.success) {
            alert(result.message);
            location.reload(); // Recargar la página para reflejar los cambios
        } else {
            alert(`Error: ${result.message}`);
        }
    } catch (error) {
        console.error('Error al editar el empleado:', error);
        alert('Ocurrió un error al editar el empleado.');
    }
});