(() => {
  const inlineChatButton = document.querySelector("[data-start-inline-chat]");
  inlineChatButton?.addEventListener("click", () => {
    const inlineFrame = inlineChatButton.parentElement.querySelector("iframe");
    inlineFrame.src = inlineFrame.dataset.src;
    inlineFrame.hidden = false;
    inlineChatButton.hidden = true;
  });
  const button = document.getElementById("portfolio-chat-button");
  const panel = document.getElementById("portfolio-chat-panel");

  const closeButton = panel.querySelector(".portfolio-chat__close");
  const frame = panel.querySelector(".portfolio-chat__frame");

  function setChatOpen(isOpen) {
    if (isOpen && !frame.hasAttribute("src")) {
      frame.src = frame.dataset.src;
    }
    panel.hidden = !isOpen;
    button.setAttribute("aria-expanded", String(isOpen));
    button.setAttribute("aria-label", isOpen ? "Close chat" : "Open chat");
    (isOpen ? closeButton : button).focus({ preventScroll: true });
  }

  button.addEventListener("click", () => setChatOpen(panel.hidden));
  closeButton.addEventListener("click", () => setChatOpen(false));
  panel.addEventListener("keydown", event => {
    if (event.key === "Escape") setChatOpen(false);
  });
})();
