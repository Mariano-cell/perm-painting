// 1) Buscamos el header en el DOM
const header = document.querySelector('.site-header');

// 2) Seguridad: si no existe, salimos
if (header) {
    // 3) Umbrales (en px)
    const SCROLL_TRIGGER = 20;   // efecto 1: color/blur (tu actual)
    const COMPACT_TRIGGER = 90;  // efecto 2: shrink (posterior)

    // 4) Función que actualiza las clases según el scroll actual
    const updateHeaderState = () => {
        const y = window.scrollY || document.documentElement.scrollTop;

        // Efecto 1
        header.classList.toggle('is-scrolled', y > SCROLL_TRIGGER);

        // Efecto 2 (posterior)
        header.classList.toggle('is-compact', y > COMPACT_TRIGGER);
    };

    // 5) Ejecutamos una vez al cargar
    updateHeaderState();

    // 6) Escuchamos scroll
    window.addEventListener('scroll', updateHeaderState, { passive: true });
}
