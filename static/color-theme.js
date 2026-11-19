(() => {
    const root = document.documentElement;
    const storageKey = `portfolio.${document.currentScript.dataset.themeScope}.theme`;

    let theme = "dark";
    try {
        if (localStorage.getItem(storageKey) === "light") theme = "light";
    } catch {
        // The current page can still switch themes if storage is unavailable.
    }
    root.dataset.theme = theme;

    document.addEventListener("DOMContentLoaded", () => {
        const button = document.querySelector("[data-color-theme-toggle]");
        if (!button) return;

        function applyTheme(value) {
            const light = value === "light";
            root.dataset.theme = light ? "light" : "dark";
            button.setAttribute("aria-pressed", String(light));
            button.title = light ? "Switch to dark mode" : "Switch to light mode";
        }

        applyTheme(theme);
        button.hidden = false;
        button.addEventListener("click", () => {
            applyTheme(root.dataset.theme === "light" ? "dark" : "light");
            try {
                localStorage.setItem(storageKey, root.dataset.theme);
            } catch {
                // The page has already updated.
            }
        });
        window.addEventListener("storage", event => {
            if (event.key === storageKey) applyTheme(event.newValue);
        });
    });
})();
