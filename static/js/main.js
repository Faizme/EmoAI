document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(msg => {
        setTimeout(() => {
            msg.style.animation = 'slideOutRight 0.3s ease-out forwards';
            setTimeout(() => msg.remove(), 300);
        }, 5000);
    });
    
    const inputs = document.querySelectorAll('.glass-input');
    inputs.forEach(input => {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && this.tagName.toLowerCase() !== 'textarea') {
                e.preventDefault();
                const form = this.closest('form');
                if (form) form.submit();
            }
        });
    });
});

document.addEventListener('mousemove', (e) => {
    const shapes = document.querySelector('.floating-shapes');
    if (shapes) {
        const x = e.clientX / window.innerWidth;
        const y = e.clientY / window.innerHeight;
        shapes.style.transform = `translate(${x * 20}px, ${y * 20}px)`;
    }
});
