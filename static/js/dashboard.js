
document.addEventListener("DOMContentLoaded", () => {
    const menuButton = document.getElementById("mobileMenuBtn");
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("sidebarOverlay");
    const menuIcon = document.getElementById("menuIcon");

    // Check that all required HTML elements exist
    if (!menuButton || !sidebar || !overlay || !menuIcon) {
        console.error("Mobile menu elements are missing.");
        return;
    }

    // Open or close the sidebar
    function setMenuOpen(open) {
        sidebar.classList.toggle("is-open", open);
        overlay.classList.toggle("is-visible", open);
        document.body.classList.toggle("menu-open", open);

        menuButton.setAttribute("aria-expanded", String(open));
        menuButton.setAttribute(
            "aria-label",
            open ? "Close navigation menu" : "Open navigation menu"
        );

        // Show X when open, three lines when closed
        menuIcon.innerHTML = open
            ? '<path d="M18 6 6 18M6 6l12 12"/>'
            : '<path d="M4 6h16M4 12h16M4 18h16"/>';
    }

    // Tap hamburger to toggle the menu
    menuButton.addEventListener("click", () => {
        const isOpen = sidebar.classList.contains("is-open");
        setMenuOpen(!isOpen);
    });

    // Tap outside the sidebar to close it
    overlay.addEventListener("click", () => {
        setMenuOpen(false);
    });

    // Close menu after selecting a link
    sidebar.querySelectorAll("a").forEach(link => {
        link.addEventListener("click", () => {
            setMenuOpen(false);
        });
    });

    // Close menu with the Escape key
    document.addEventListener("keydown", event => {
        if (event.key === "Escape") {
            setMenuOpen(false);
        }
    });

    // Close/reset the menu when switching to desktop width
    window.addEventListener("resize", () => {
        if (window.innerWidth > 640) {
            setMenuOpen(false);
        }
    });
});
