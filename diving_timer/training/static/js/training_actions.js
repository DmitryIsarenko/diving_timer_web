(function () {
  "use strict";

  var forms = document.querySelectorAll("[data-training-action]");

  forms.forEach(function (form) {
    form.addEventListener("submit", function (event) {
      if (form.dataset.submitting === "true") {
        event.preventDefault();
        return;
      }

      if (!window.confirm(form.dataset.confirmMessage)) {
        event.preventDefault();
        return;
      }

      form.dataset.submitting = "true";
      form.querySelectorAll('button[type="submit"]').forEach(function (button) {
        button.disabled = true;
      });
    });
  });

  // A cached page must remain usable when navigating back after a POST.
  window.addEventListener("pageshow", function () {
    forms.forEach(function (form) {
      delete form.dataset.submitting;
      form.querySelectorAll('button[type="submit"]').forEach(function (button) {
        button.disabled = false;
      });
    });
  });
})();