(() => {
  const wizard = document.querySelector(".service-wizard");
  if (!wizard) return;
  const steps = [...wizard.querySelectorAll(".step")];
  const bars = [...wizard.querySelectorAll(".wizard-progress i")];
  let current = 0;
  function show(index) {
    current = index;
    steps.forEach((step, i) => step.classList.toggle("active", i === index));
    bars.forEach((bar, i) => bar.classList.toggle("on", i <= index));
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
  wizard.querySelectorAll(".wizard-next").forEach((button) =>
    button.addEventListener("click", () => {
      const fields = [...steps[current].querySelectorAll("[required]")];
      if (fields.every((field) => field.reportValidity()))
        show(Math.min(current + 1, steps.length - 1));
    }),
  );
  wizard
    .querySelectorAll(".wizard-back")
    .forEach((button) =>
      button.addEventListener("click", () => show(Math.max(current - 1, 0))),
    );
})();
