(() => {
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

    function setupMenu() {
        const toggle = document.querySelector("[data-menu-toggle]");
        const nav = toggle?.closest(".nav");
        const links = nav?.querySelector(".nav-links");

        if (!links) {
            return;
        }

        function setOpen(open) {
            nav.classList.toggle("menu-open", open);
            toggle.setAttribute("aria-expanded", String(open));
        }

        nav.classList.add("menu-ready");
        setOpen(false);

        toggle.addEventListener("click", () => setOpen(!nav.classList.contains("menu-open")));
        links.addEventListener("click", (event) => {
            if (event.target.closest("a")) {
                setOpen(false);
            }
        });
        document.addEventListener("click", (event) => {
            if (nav.classList.contains("menu-open") && !nav.contains(event.target)) {
                setOpen(false);
            }
        });
        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape" && nav.classList.contains("menu-open")) {
                setOpen(false);
                toggle.focus();
            }
        });
    }

    function setupReveals() {
        if (reducedMotion.matches || !("IntersectionObserver" in window)) {
            return;
        }

        const pending = new Set();
        const observer = new IntersectionObserver((entries) => {
            for (const entry of entries) {
                if (entry.isIntersecting) {
                    show(entry.target);
                }
            }
        }, { rootMargin: "0px 0px -8% 0px" });

        function show(element, immediate = false) {
            if (immediate) {
                element.classList.remove("will-reveal");
            }
            element.classList.add("is-visible");
            observer.unobserve(element);
            pending.delete(element);
        }

        function hashTarget() {
            try {
                return document.getElementById(decodeURIComponent(location.hash.slice(1)));
            } catch {
                return null;
            }
        }

        function containsHash(element, target) {
            return target && (element.contains(target) || target.contains(element));
        }

        const initialTarget = hashTarget();
        for (const element of document.querySelectorAll("[data-reveal]")) {
            if (element.getBoundingClientRect().top < window.innerHeight ||
                element.contains(document.activeElement) || containsHash(element, initialTarget)) {
                continue;
            }

            element.classList.add("will-reveal");
            pending.add(element);
            observer.observe(element);
        }

        document.addEventListener("focusin", (event) => {
            for (const element of pending) {
                if (element.contains(event.target)) {
                    show(element, true);
                }
            }
        });
        window.addEventListener("hashchange", () => {
            const target = hashTarget();
            for (const element of pending) {
                if (containsHash(element, target)) {
                    show(element, true);
                }
            }
        });
        reducedMotion.addEventListener("change", () => {
            if (reducedMotion.matches) {
                for (const element of pending) {
                    show(element, true);
                }
            }
        });
    }

    function setupCounters() {
        if (reducedMotion.matches || !("IntersectionObserver" in window)) {
            return;
        }

        const active = new Map();
        const observer = new IntersectionObserver((entries) => {
            for (const entry of entries) {
                if (entry.isIntersecting && !reducedMotion.matches) {
                    observer.unobserve(entry.target);
                    animate(entry.target);
                }
            }
        }, { threshold: 0.35 });

        function finish(element, animation) {
            cancelAnimationFrame(animation.frame);
            element.textContent = animation.finalText;
            active.delete(element);
        }

        function animate(element) {
            const value = Number(element.dataset.count);
            const digits = element.dataset.count.split(".")[1]?.length ?? 0;
            const suffix = element.dataset.suffix ?? "";
            const animation = { finalText: element.textContent, frame: 0 };
            const start = performance.now();

            function tick(now) {
                const progress = Math.min((now - start) / 900, 1);
                if (progress === 1 || reducedMotion.matches) {
                    finish(element, animation);
                    return;
                }

                const eased = 1 - (1 - progress) ** 3;
                element.textContent = `${(value * eased).toFixed(digits)}${suffix}`;
                animation.frame = requestAnimationFrame(tick);
            }

            active.set(element, animation);
            element.textContent = `${(0).toFixed(digits)}${suffix}`;
            animation.frame = requestAnimationFrame(tick);
        }

        for (const element of document.querySelectorAll("[data-count]")) {
            if (/^-?\d+(?:\.\d{1,3})?$/.test(element.dataset.count)) {
                observer.observe(element);
            }
        }

        reducedMotion.addEventListener("change", () => {
            if (reducedMotion.matches) {
                observer.disconnect();
                for (const [element, animation] of active) {
                    finish(element, animation);
                }
            }
        });
    }

    function setupCardGlow() {
        const finePointer = window.matchMedia("(hover: hover) and (pointer: fine)");
        const cards = document.querySelectorAll("[data-card-glow]");

        function reset(card) {
            card.style.removeProperty("--glow-x");
            card.style.removeProperty("--glow-y");
        }

        for (const card of cards) {
            card.addEventListener("pointermove", (event) => {
                if (reducedMotion.matches || !finePointer.matches || event.pointerType === "touch") {
                    return;
                }

                const bounds = card.getBoundingClientRect();
                const x = (event.clientX - bounds.left) / bounds.width * 100;
                const y = (event.clientY - bounds.top) / bounds.height * 100;
                card.style.setProperty("--glow-x", `${x.toFixed(2)}%`);
                card.style.setProperty("--glow-y", `${y.toFixed(2)}%`);
            });
            card.addEventListener("pointerleave", () => reset(card));
            card.addEventListener("pointercancel", () => reset(card));
        }

        reducedMotion.addEventListener("change", () => cards.forEach(reset));
        finePointer.addEventListener("change", () => cards.forEach(reset));
    }

    setupMenu();
    setupReveals();
    setupCounters();
    setupCardGlow();
})();
