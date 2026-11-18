document.querySelectorAll("[data-confirm-delete]").forEach((form) => {
    form.addEventListener("submit", (event) => {
        if (!window.confirm("Delete this expense?")) {
            event.preventDefault();
        }
    });
});
