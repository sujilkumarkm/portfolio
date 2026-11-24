document.addEventListener("DOMContentLoaded", () => {
    const dialog = document.querySelector(".interview-question-preview");
    const triggers = [...document.querySelectorAll("[data-interview-question-preview]")];
    if (!dialog || !triggers.length) return;

    const frame = dialog.querySelector("iframe");
    const title = dialog.querySelector("h2");
    const download = dialog.querySelector(".document-preview-download");
    const previous = dialog.querySelector("[data-interview-preview-previous]");
    const next = dialog.querySelector("[data-interview-preview-next]");
    const position = dialog.querySelector("[data-interview-preview-position]");
    let activeIndex = 0;

    const showSlide = index => {
        activeIndex = index;
        const trigger = triggers[index];
        const isWordDocument = trigger.dataset.documentFilename.toLowerCase().endsWith(".docx");
        title.textContent = trigger.dataset.documentTitle;
        if (isWordDocument) frame.setAttribute("sandbox", "");
        else frame.removeAttribute("sandbox");
        frame.src = trigger.dataset.interviewQuestionPreview;
        download.href = trigger.dataset.documentDownload;
        previous.hidden = next.hidden = position.hidden = triggers.length < 2;
        previous.disabled = index === 0;
        next.disabled = index === triggers.length - 1;
        position.textContent = `${index + 1} of ${triggers.length}`;
    };

    previous.addEventListener("click", () => showSlide(activeIndex - 1));
    next.addEventListener("click", () => showSlide(activeIndex + 1));
    triggers.forEach((trigger, index) => {
        trigger.addEventListener("click", () => {
            showSlide(index);
            dialog.showModal();
        });
    });
    dialog.addEventListener("close", () => frame.removeAttribute("src"));
});
