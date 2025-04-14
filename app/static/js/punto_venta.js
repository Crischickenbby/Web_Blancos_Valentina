let sidebar = document.querySelector(".sidebar");
let closeBtn = document.querySelector("#btn");
let searchBtn = document.querySelector(".bx-search");

// Asegurarse de que el sidebar esté cerrado al cargar la página
document.addEventListener("DOMContentLoaded", () => {
    if (sidebar) {
        sidebar.classList.remove("open"); // Cambiar a remove para que esté cerrado
    }
});

// Función para cambiar el icono del menú
function menuBtnChange() {
    if (sidebar.classList.contains("open")) {
        closeBtn.classList.replace("bx-menu", "bx-menu-alt-right");
    } else {
        closeBtn.classList.replace("bx-menu-alt-right", "bx-menu");
    }
}

// Evento para abrir/cerrar el sidebar con el botón de menú
closeBtn.addEventListener("click", () => {
    sidebar.classList.toggle("open");
    menuBtnChange();
});

// Evento para asegurarse de que el botón de búsqueda solo abre el sidebar
searchBtn.addEventListener("click", () => {
    if (!sidebar.classList.contains("open")) {
        sidebar.classList.add("open");
        menuBtnChange();
    }
});

// Prevenir que los enlaces dentro del sidebar recarguen la página
document.querySelectorAll(".nav-list a").forEach(link => {
    link.addEventListener("click", (event) => {
        event.preventDefault(); // Evita la recarga de la página
    });
});

// Inicializar el estado del botón del menú
menuBtnChange();