"use strict";

// Forms also work without JavaScript. Enhancement keeps focus and scroll in place.
document.documentElement.classList.add("js");
let pending = Promise.resolve();

document.addEventListener("change", (event) => {
  if (event.target.matches("#app select")) event.target.form.requestSubmit();
});

document.addEventListener("submit", (event) => {
  const form = event.target;
  if (!form.matches("#app form")) return;
  event.preventDefault();
  const data = new URLSearchParams(new FormData(form, event.submitter));
  const focusId = (event.submitter || document.activeElement).id;
  pending = pending.then(async () => {
    const app = document.getElementById("app");
    const error = document.getElementById("request-error");
    app.setAttribute("aria-busy", "true");
    try {
      const response = await fetch("/", { method: "POST", body: data });
      if (!response.ok) throw new Error("Selection request failed");
      const next = new DOMParser().parseFromString(await response.text(), "text/html");
      const replacement = next.getElementById("app");
      if (!replacement) throw new Error("Selection response missing");
      app.replaceWith(replacement);
      document.getElementById("state-summary").textContent =
        next.getElementById("state-summary").textContent;
      document.getElementById(focusId)?.focus({ preventScroll: true });
      error.hidden = true;
    } catch {
      error.textContent = "The selection could not be applied. Try the control again, or reload the page.";
      error.hidden = false;
    } finally {
      document.getElementById("app").removeAttribute("aria-busy");
    }
  });
});
