/* Progressive enhancement: keep the static background until video can play. */
(() => {
    const script = document.currentScript;
    if (!script) return;
    const videoURL = new URL('../assets/meadow-background.mp4', script.src).href;
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    const connection = navigator.connection;
    let video;
    let button;
    let userPaused = false;
    const shouldStayStatic = () => reducedMotion.matches || connection?.saveData;

    function updateButton() {
        button.textContent = video.paused ? '播放背景' : '暂停背景';
        button.setAttribute('aria-label', video.paused ? '播放草地背景动画' : '暂停草地背景动画');
    }

    function play() {
        if (document.hidden || userPaused || shouldStayStatic()) return;
        video.play().catch(() => {
            video.classList.remove('is-playing');
            button.hidden = false;
            updateButton();
        });
    }

    function sync() {
        if (shouldStayStatic()) {
            if (video) {
                video.pause();
                video.removeAttribute('src');
                video.load();
                video.classList.remove('is-playing');
                button.hidden = true;
            }
            return;
        }
        if (document.hidden) {
            video?.pause();
            return;
        }
        if (!video) {
            video = document.createElement('video');
            video.className = 'ambient-video';
            video.muted = true;
            video.defaultMuted = true;
            video.loop = true;
            video.playsInline = true;
            video.preload = 'none';
            video.setAttribute('muted', '');
            video.setAttribute('playsinline', '');
            video.setAttribute('aria-hidden', 'true');
            video.tabIndex = -1;
            button = document.createElement('button');
            button.className = 'ambient-toggle';
            button.type = 'button';
            button.hidden = true;
            button.addEventListener('click', () => {
                userPaused = !video.paused;
                if (userPaused) video.pause();
                else play();
            });
            video.addEventListener('playing', () => {
                video.classList.add('is-playing');
                button.hidden = false;
                updateButton();
            });
            video.addEventListener('pause', updateButton);
            video.addEventListener('error', () => {
                video.classList.remove('is-playing');
                button.hidden = true;
            });
            document.body.prepend(video);
            document.body.append(button);
        }
        if (!video.getAttribute('src')) video.src = videoURL;
        play();
    }

    function start() {
        sync();
        document.addEventListener('visibilitychange', sync);
        reducedMotion.addEventListener('change', sync);
        connection?.addEventListener?.('change', sync);
    }
    // Low-priority work begins only after the initial page assets finish loading.
    function schedule() {
        if ('requestIdleCallback' in window) window.requestIdleCallback(start, { timeout: 1500 });
        else window.setTimeout(start, 250);
    }
    if (document.readyState === 'complete') schedule();
    else window.addEventListener('load', schedule, { once: true });
})();
