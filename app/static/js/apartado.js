document.addEventListener('DOMContentLoaded', function () {
    const addLayawayBtn = document.getElementById('addLayawayBtn');
    const managePaymentsBtn = document.getElementById('managePaymentsBtn');
    const addLayawayModal = document.getElementById('addLayawayModal');
    const managePaymentsModal = document.getElementById('managePaymentsModal');
    const closeButtons = document.querySelectorAll('.close-button');

    // Abrir modal de añadir apartado
    addLayawayBtn.addEventListener('click', () => {
        addLayawayModal.style.display = 'block';
    });

    // Abrir modal de gestionar pagos
    managePaymentsBtn.addEventListener('click', () => {
        managePaymentsModal.style.display = 'block';
    });

    // Cerrar modales
    closeButtons.forEach(button => {
        button.addEventListener('click', () => {
            addLayawayModal.style.display = 'none';
            managePaymentsModal.style.display = 'none';
        });
    });

    // Cerrar modal al hacer clic fuera del contenido
    window.addEventListener('click', (event) => {
        if (event.target === addLayawayModal) {
            addLayawayModal.style.display = 'none';
        }
        if (event.target === managePaymentsModal) {
            managePaymentsModal.style.display = 'none';
        }
    });
});