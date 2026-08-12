// Mobile navigation ----------------------------------------------------------
// Keep this intentionally small for the MVP; server-rendered pages handle most UX.
const menuButton = document.querySelector("#menu");
const mobileNav = document.querySelector("#mobileNav");

if (menuButton && mobileNav) {
  menuButton.addEventListener("click", () => {
    mobileNav.classList.toggle("open");
  });
}

// File upload feedback -------------------------------------------------------
// Store the selected filename on the input so CSS/future UI can surface it.
document.querySelectorAll('input[type="file"]').forEach((input) => {
  input.addEventListener("change", () => {
    const [selectedFile] = input.files;

    if (selectedFile) {
      input.dataset.selected = selectedFile.name;
    }
  });
});
