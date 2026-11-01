document.querySelectorAll("[data-notification]").forEach((notification) => {
    let dismissTimer;

    const dismiss = () => {
        notification.classList.add("is-dismissing");
        window.setTimeout(() => notification.remove(), 250);
    };

    const startDismissTimer = () => {
        window.clearTimeout(dismissTimer);
        dismissTimer = window.setTimeout(dismiss, 5000);
    };

    notification
        .querySelector("[data-notification-close]")
        .addEventListener("click", dismiss);

    notification.addEventListener("mouseenter", () => {
        window.clearTimeout(dismissTimer);
    });
    notification.addEventListener("mouseleave", startDismissTimer);
    notification.addEventListener("focusin", () => {
        window.clearTimeout(dismissTimer);
    });
    notification.addEventListener("focusout", startDismissTimer);

    startDismissTimer();
});
