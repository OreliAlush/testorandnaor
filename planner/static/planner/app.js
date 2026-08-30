(() => {
  const steps = [...document.querySelectorAll(".step")];
  const progress = [...document.querySelectorAll(".progress i")];
  let current = 0;
  function show(index) {
    current = index;
    steps.forEach((s, i) => s.classList.toggle("active", i === current));
    progress.forEach((p, i) => p.classList.toggle("on", i <= current));
    if (current === 4) calculate();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
  function validStep() {
    return [...steps[current].querySelectorAll("[required]")].every((el) => {
      const valid = el.reportValidity();
      return valid;
    });
  }
  document
    .querySelectorAll(".next")
    .forEach(
      (b) => (b.onclick = () => validStep() && show(Math.min(current + 1, 4))),
    );
  document
    .querySelectorAll(".back")
    .forEach((b) => (b.onclick = () => show(Math.max(current - 1, 0))));
  function calculate() {}
  const fileInput = document.querySelector("#spacePhoto");
  const planner = document.querySelector("#photoPlanner");
  const preview = document.querySelector("#photoPreview");
  const help = document.querySelector("#plannerHelp");
  const overlay = document.querySelector("#planOverlay");
  let corners = [];
  function drawPlan() {
    overlay.innerHTML = "";
    if (corners.length > 1)
      overlay.innerHTML += `<polygon points="${corners.map((point) => `${point.x},${point.y}`).join(" ")}"></polygon>`;
    corners.forEach(
      (point, i) =>
        (overlay.innerHTML += `<circle cx="${point.x}" cy="${point.y}" r="2.2"></circle><text x="${+point.x + 3}" y="${+point.y - 3}" fill="white" font-size="5">${i + 1}</text>`),
    );
  }
  fileInput.addEventListener("change", () => {
    const file = fileInput.files[0];
    if (!file) return;
    if (file.size > 10 * 1024 * 1024) {
      alert("נא לבחור תמונה עד 10MB");
      fileInput.value = "";
      return;
    }
    preview.src = URL.createObjectURL(file);
    corners = [];
    drawPlan();
    planner.classList.remove("hidden");
    help.classList.remove("hidden");
  });
  planner.addEventListener("click", (event) => {
    if (!preview.src || corners.length === 4) return;
    const rect = planner.getBoundingClientRect();
    corners.push({
      x: (((event.clientX - rect.left) / rect.width) * 100).toFixed(2),
      y: (((event.clientY - rect.top) / rect.height) * 100).toFixed(2),
    });
    drawPlan();
  });
  document.querySelector("#resetCorners").addEventListener("click", () => {
    corners = [];
    drawPlan();
  });
})();
