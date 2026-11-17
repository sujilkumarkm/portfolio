document.addEventListener("DOMContentLoaded", () => {
    const dialog = document.querySelector(".document-preview");
    if (dialog) {
        const frame = dialog.querySelector("iframe");
        const title = dialog.querySelector("h2");
        const download = dialog.querySelector(".document-preview-download");
        const previous = dialog.querySelector("[data-preview-previous]");
        const next = dialog.querySelector("[data-preview-next]");
        const position = dialog.querySelector("[data-preview-position]");
        let slides = [];
        let activeIndex = 0;
        const showSlide = index => {
            activeIndex = index;
            const slide = slides[index];
            title.textContent = slide.dataset.documentTitle;
            frame.src = slide.dataset.previewDocument;
            download.href = slide.closest(".saved-document").querySelector("a").href;
            previous.hidden = next.hidden = position.hidden = slides.length < 2;
            previous.disabled = index === 0;
            next.disabled = index === slides.length - 1;
            position.textContent = `${index + 1} of ${slides.length}`;
            if (!matchMedia("(prefers-reduced-motion: reduce)").matches) {
                frame.animate([{opacity: .3}, {opacity: 1}], {duration: 220});
            }
        };
        previous.addEventListener("click", () => showSlide(activeIndex - 1));
        next.addEventListener("click", () => showSlide(activeIndex + 1));
        for (const button of document.querySelectorAll("[data-preview-document]")) {
            button.addEventListener("click", () => {
                slides = [...document.querySelectorAll("[data-preview-document]")];
                dialog.showModal();
                showSlide(slides.indexOf(button));
            });
        }
        dialog.addEventListener("close", () => frame.removeAttribute("src"));
    }

    for (const button of document.querySelectorAll("[data-remove-document]")) {
        const row = button.closest(".saved-document");
        const status = document.createElement("span");
        status.setAttribute("role", "status");
        row.append(status);
        button.addEventListener("click", async () => {
            const label = button.textContent;
            if (!window.confirm(`${label} from this application?`)) return;

            button.disabled = true;
            status.textContent = " Removing…";
            try {
                const csrf = button.form.elements.namedItem("csrfmiddlewaretoken").value;
                const response = await fetch(button.dataset.removeDocument, {
                    method: "POST", headers: {"X-CSRFToken": csrf},
                });
                if (!response.ok || !(await response.json()).removed) throw new Error();
                row.querySelector("a").remove();
                row.querySelector("[data-preview-document]")?.remove();
                status.textContent = `${label.replace("Remove ", "")} removed.`;
                status.tabIndex = -1;
                status.focus();
                button.remove();
            } catch {
                status.textContent = " Could not remove this file. Refresh the page or try again.";
                button.disabled = false;
            }
        });
    }
});
