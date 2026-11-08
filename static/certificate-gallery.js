const certificateGallery = document.querySelector("#certificate-gallery");

if (certificateGallery && typeof certificateGallery.showModal === "function") {
    document.querySelectorAll("[data-certificate-preview]").forEach((trigger) => {
        trigger.setAttribute("aria-haspopup", "dialog");
        trigger.addEventListener("click", (event) => {
            if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) {
                return;
            }

            event.preventDefault();
            certificateGallery.showModal();
        });
    });

    certificateGallery.addEventListener("click", (event) => {
        if (event.target === certificateGallery) {
            certificateGallery.close();
        }
    });
}
