const images = document.querySelectorAll("#carousel img");
let currentIndex = 0;

setInterval(() => {
  console.log("Cambiando imagen..."); // Depuración
  images[currentIndex].classList.remove("active");
  currentIndex = (currentIndex + 1) % images.length;
  images[currentIndex].classList.add("active");
}, 3000);