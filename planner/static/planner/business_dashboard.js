document.querySelectorAll("[data-copy-link]").forEach((button) => {
  button.addEventListener("click", async () => {
    const input = document.getElementById(button.dataset.copyLink);
    try {
      await navigator.clipboard.writeText(input.value);
      button.textContent = "הקישור הועתק ✓";
    } catch (_) {
      input.focus();
      input.select();
      button.textContent = "הקישור סומן — אפשר להעתיק";
    }
  });
});
