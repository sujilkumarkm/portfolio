const consent = document.querySelector("#visitor-consent");
const preferences = document.querySelector("#visitor-settings");

if (consent && preferences) {
    const form = consent.querySelector("form");
    const status = form.querySelector("[role=status]");
    const key = "portfolio-analytics-choice-v2";
    const submit = async choice => {
        const data = new FormData(form);
        data.set("choice", choice);
        const response = await fetch(form.action, {method: "POST", body: data, credentials: "same-origin"});
        if (!response.ok) throw new Error("Could not save analytics preferences");
    };

    let saved;
    try {
        saved = localStorage.getItem(key);
    } catch {
        // Preferences can still be used while this page is open.
    }
    preferences.hidden = false;
    consent.hidden = saved === "allow" || saved === "decline";
    if (saved === "allow") submit("allow").catch(() => {});
    preferences.addEventListener("click", () => {
        consent.hidden = !consent.hidden;
        if (!consent.hidden) form.querySelector("button").focus({ preventScroll: true });
    });
    form.addEventListener("submit", async event => {
        event.preventDefault();
        const buttons = [...form.querySelectorAll("button")];
        const choice = event.submitter?.value || "decline";
        buttons.forEach(button => { button.disabled = true; });
        try {
            await submit(choice);
            try {
                localStorage.setItem(key, choice);
            } catch {
                // The server has already applied the choice.
            }
            consent.hidden = true;
            status.textContent = "";
            preferences.focus({ preventScroll: true });
        } catch {
            status.textContent = "Could not save your preference. Please try again.";
        } finally {
            buttons.forEach(button => { button.disabled = false; });
        }
    });
}
