(() => {
    const viewport = document.querySelector('[data-gallery="taca"]');
    if (!viewport) return;

    const track = viewport.querySelector('.about-page__gallery-track');
    if (!track) return;

    const slides = Array.from(track.querySelectorAll('.about-page__slide img'));
    if (slides.length < 3) return;

    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // ✅ Poné acá tus rutas reales
    const images = [
        { src: 'assets/photos/IMG_0815.png', alt: 'Painting project photo 1' },
        { src: 'assets/photos/IMG_1045.png', alt: 'Painting project photo 2' },
        { src: 'assets/photos/IMG_9949.png', alt: 'Painting project photo 3' },
        { src: 'assets/photos/IMG_1044.png', alt: 'Painting project photo 4' },
        // { src: 'assets/img/about/about-05.jpg', alt: 'Painting project photo 5' }
    ];

    // Índice del par visible: left = i, right = i+1
    let i = 0;
    let isRunning = false;

    const setImg = (imgEl, item) => {
        imgEl.src = item.src;
        imgEl.alt = item.alt || '';
        imgEl.loading = 'lazy';
        imgEl.decoding = 'async';
    };

    const render3 = () => {
        const left = images[i % images.length];
        const right = images[(i + 1) % images.length];
        const next = images[(i + 2) % images.length];

        setImg(slides[0], left);
        setImg(slides[1], right);
        setImg(slides[2], next);

        // estado base (sin animación): se ven left+right
        track.classList.remove('is-animating', 'to-next');
        track.style.transform = 'translateX(0)';
    };

    const tick = () => {
        if (isRunning) return;
        isRunning = true;

        if (prefersReduced) {
            // sin animación: “salto” igual pero instantáneo
            i = (i + 1) % images.length;
            render3();
            isRunning = false;
            return;
        }

        // 1) activar transición
        track.classList.add('is-animating');

        // 2) forzar reflow para asegurar que el browser tome el estado base
        // eslint-disable-next-line no-unused-expressions
        track.offsetHeight;

        // 3) mover 1 slide: left sale, right pasa a left, next entra
        track.classList.add('to-next');

        const onDone = (e) => {
            if (e.propertyName !== 'transform') return;
            track.removeEventListener('transitionend', onDone);

            // 4) rotar índice
            i = (i + 1) % images.length;

            // 5) re-render de las 3 imágenes y reset sin animación
            render3();

            isRunning = false;
        };

        track.addEventListener('transitionend', onDone);
    };

    // init
    render3();

    // Autoplay “no constante”: cada 3.8s una patada
    const INTERVAL_MS = 3800;
    const timer = window.setInterval(tick, INTERVAL_MS);

    // opcional: pausar si la tab no está visible (evita saltos)
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            window.clearInterval(timer);
        }
    }, { passive: true });
})();
