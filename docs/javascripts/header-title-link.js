// Material's header only makes the small logo icon a homepage link, not the
// title text next to it. Make the title clickable too, reusing the logo's
// own href so the target stays correct locally and on GitHub Pages alike.
document$.subscribe(() => {
  const title = document.querySelector(".md-header__title");
  const logo = document.querySelector('[data-md-component="logo"]');
  if (title && logo && !title.dataset.homeLink) {
    title.dataset.homeLink = "true";
    title.style.cursor = "pointer";
    title.addEventListener("click", () => {
      window.location.href = logo.getAttribute("href");
    });
  }
});
