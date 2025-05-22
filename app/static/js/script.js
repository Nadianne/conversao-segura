const menuToggle = document.getElementById('menu-toggle');
const navbar = document.getElementById('navbar');

menuToggle.addEventListener('click', () => {
  navbar.classList.toggle('active');

  // Alterna entre ☰ (hambúrguer) e ✖ (X)
  if (menuToggle.innerHTML === "☰" || menuToggle.innerHTML === "&#9776;") {
    menuToggle.innerHTML = "✖";
  } else {
    menuToggle.innerHTML = "☰";
  }
});
