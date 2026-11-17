const menuToggle = document.querySelector(".portfolio-menu-toggle");

if (menuToggle) {
    const menu = document.getElementById(menuToggle.getAttribute("aria-controls"));
    const compact = matchMedia("(max-width: 800px)");
    const setExpanded = expanded => {
        if (!expanded && menu.contains(document.activeElement)) {
            menuToggle.focus();
        }
        menuToggle.setAttribute("aria-expanded", String(expanded));
    };
    const syncLayout = () => setExpanded(!compact.matches);

    menuToggle.hidden = false;
    syncLayout();
    compact.addEventListener("change", syncLayout);
    menuToggle.addEventListener("click", () => {
        setExpanded(menuToggle.getAttribute("aria-expanded") === "false");
    });
    menu.addEventListener("keydown", event => {
        if (event.key === "Escape" && compact.matches) {
            setExpanded(false);
        }
    });
}
