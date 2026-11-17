document.addEventListener("DOMContentLoaded", () => {
    const button = document.querySelector("[data-job-import]");
    const urlInput = document.getElementById("id_posting_url");
    if (!button || !urlInput) return;

    const panel = button.closest(".job-import");
    const status = panel.querySelector("[role=status]");
    const csrf = button.form.elements.namedItem("csrfmiddlewaretoken").value;
    urlInput.closest(".form-row")?.after(panel);
    panel.hidden = false;

    button.addEventListener("click", async () => {
        const url = urlInput.value.trim();
        if (!url) {
            status.textContent = "Enter a posting URL first.";
            urlInput.focus();
            return;
        }
        button.disabled = true;
        status.textContent = "Reading the job posting…";
        try {
            const response = await fetch(button.dataset.jobImport, {
                method: "POST",
                body: new URLSearchParams({url}),
                headers: {"X-CSRFToken": csrf},
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.error);
            if (urlInput.value.trim() !== url) {
                status.textContent = "The URL changed. Import again to use the new posting.";
                return;
            }
            let filled = 0;
            for (const [field, value] of Object.entries(result.fields)) {
                const input = document.getElementById(`id_${field}`);
                if (input && !input.value.trim()) {
                    input.value = value;
                    filled += 1;
                }
            }
            status.textContent = filled
                ? "Available details were added to the blank fields. Review them before saving."
                : "The fields available from this posting are already filled in.";
        } catch (error) {
            status.textContent = error instanceof SyntaxError || error instanceof TypeError
                ? "Could not import the posting. Try again or enter the details manually."
                : error.message;
        } finally {
            button.disabled = false;
        }
    });
});
