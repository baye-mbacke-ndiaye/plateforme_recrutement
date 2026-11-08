/* KayJoop — scripts du site (un seul fichier) */
document.addEventListener("DOMContentLoaded", () => {

    /* Menu mobile */
    const burger = document.querySelector("[data-burger]");
    const menu = document.getElementById("menu");
    if (burger && menu) {
        burger.addEventListener("click", () => {
            const ouvert = menu.classList.toggle("is-open");
            burger.setAttribute("aria-expanded", String(ouvert));
            burger.setAttribute("aria-label", ouvert ? "Fermer le menu" : "Ouvrir le menu");
        });
    }

    document.querySelectorAll("[data-file-picker]").forEach((picker) => {
        const input = picker.querySelector('input[type="file"]');
        const clearButton = picker.querySelector("[data-clear-file]");
        const fileName = picker.querySelector("[data-file-name]");
        if (!input || !clearButton || !fileName) return;

        const updateSelection = () => {
            const file = input.files && input.files[0];
            fileName.textContent = file ? file.name : "";
            clearButton.hidden = !file;
        };

        input.addEventListener("change", updateSelection);
        clearButton.addEventListener("click", () => {
            input.value = "";
            updateSelection();
            input.focus();
        });
    });

    /* Retour en haut de page */
    const haut = document.querySelector("[data-top]");
    if (haut) {
        haut.addEventListener("click", (event) => {
            event.preventDefault();
            window.scrollTo({ top: 0, behavior: "smooth" });
        });
    }

    /* Afficher / masquer un mot de passe */
    document.addEventListener("click", (event) => {
        const bouton = event.target.closest("[data-toggle-password]");
        if (!bouton) return;
        const champ = bouton.parentElement.querySelector("input");
        if (!champ) return;
        const visible = champ.type === "password";
        champ.type = visible ? "text" : "password";
        bouton.textContent = visible ? "Masquer" : "Afficher";
        bouton.setAttribute("aria-pressed", String(visible));
        bouton.setAttribute("aria-label", visible ? "Masquer le mot de passe" : "Afficher le mot de passe");
    });

    /* Confirmation avant une action sensible : <form data-confirm="..."> */
    document.addEventListener("submit", (event) => {
        const message = event.target.getAttribute("data-confirm");
        if (message && !window.confirm(message)) event.preventDefault();
    });

    /* Copier un texte : <button data-copy="#id"> */
    document.addEventListener("click", (event) => {
        const bouton = event.target.closest("[data-copy]");
        if (!bouton) return;
        const source = document.querySelector(bouton.getAttribute("data-copy"));
        if (source && navigator.clipboard) {
            navigator.clipboard.writeText(source.textContent.trim());
            bouton.textContent = "Copié";
        }
    });

    /* Notifications : fermeture automatique après 5 secondes */
    document.querySelectorAll("[data-notification]").forEach((notification) => {
        let minuteur;
        const fermer = () => {
            notification.classList.add("is-dismissing");
            window.setTimeout(() => notification.remove(), 250);
        };
        const demarrer = () => {
            window.clearTimeout(minuteur);
            minuteur = window.setTimeout(fermer, 5000);
        };
        notification.querySelector("[data-notification-close]").addEventListener("click", fermer);
        notification.addEventListener("mouseenter", () => window.clearTimeout(minuteur));
        notification.addEventListener("mouseleave", demarrer);
        notification.addEventListener("focusin", () => window.clearTimeout(minuteur));
        notification.addEventListener("focusout", demarrer);
        demarrer();
    });
});
