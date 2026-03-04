/**
 * AirAware - Ambient Floating Particles Animation
 * Creates a subtle, persistent particle effect across the site
 */

(function () {
    const canvas = document.createElement('canvas');
    canvas.id = 'particleCanvas';
    canvas.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:1;opacity:0.85;';
    document.body.prepend(canvas);

    const ctx = canvas.getContext('2d');
    let particles = [];
    let animationId;
    let w, h;

    function resize() {
        w = canvas.width = window.innerWidth;
        h = canvas.height = window.innerHeight;
    }

    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            resize();
            // Re-initialize particles on resize to adjust density/position if needed
            // For now, simpler reset:
            w = canvas.width = window.innerWidth;
            h = canvas.height = window.innerHeight;
        }, 200);
    });
    resize();

    // Particle count based on screen size
    const count = Math.min(Math.floor((w * h) / 12000), 80);

    class Particle {
        constructor() {
            this.reset();
            // Start at random position (not just top)
            this.y = Math.random() * h;
        }

        reset() {
            this.x = Math.random() * w;
            this.y = -10;
            this.size = Math.random() * 3 + 0.8;
            this.speedY = Math.random() * 0.3 + 0.1;
            this.speedX = (Math.random() - 0.5) * 0.4;
            this.opacity = Math.random() * 0.5 + 0.3;
            this.pulse = Math.random() * Math.PI * 2;
            this.pulseSpeed = Math.random() * 0.015 + 0.005;
            // Subtle color variation (white to light blue/purple)
            const hue = Math.random() * 60 + 220; // 220-280 range (blue to purple)
            const sat = Math.random() * 40 + 30;
            const light = Math.random() * 15 + 80;
            this.color = `hsla(${hue}, ${sat}%, ${light}%, `;
        }

        update() {
            this.y += this.speedY;
            this.x += this.speedX + Math.sin(this.pulse) * 0.15;
            this.pulse += this.pulseSpeed;

            // Gentle floating oscillation
            const currentOpacity = this.opacity * (0.6 + 0.4 * Math.sin(this.pulse));

            if (this.y > h + 10 || this.x < -10 || this.x > w + 10) {
                this.reset();
            }

            return currentOpacity;
        }

        draw(opacity) {
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fillStyle = this.color + opacity + ')';
            ctx.fill();

            // Subtle glow on larger particles
            if (this.size > 1.5) {
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.size * 2.5, 0, Math.PI * 2);
                ctx.fillStyle = this.color + (opacity * 0.15) + ')';
                ctx.fill();
            }
        }
    }

    // Initialize particles
    for (let i = 0; i < count; i++) {
        particles.push(new Particle());
    }

    function animate() {
        ctx.clearRect(0, 0, w, h);

        for (const p of particles) {
            const opacity = p.update();
            p.draw(opacity);
        }

        animationId = requestAnimationFrame(animate);
    }

    // Start animation - pause when tab is hidden for performance
    animate();

    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            cancelAnimationFrame(animationId);
        } else {
            animate();
        }
    });
})();
