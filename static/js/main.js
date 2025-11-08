// Parallax mouse effect
document.addEventListener('mousemove', (e) => {
    const moveX = (e.clientX / window.innerWidth - 0.5) * 20;
    const moveY = (e.clientY / window.innerHeight - 0.5) * 20;
    
    // Move orbs with parallax
    const orbs = document.querySelectorAll('.orb');
    orbs.forEach((orb, index) => {
        const speed = (index + 1) * 0.5;
        orb.style.transform = `translate(${moveX * speed}px, ${moveY * speed}px)`;
    });
    
    // Tilt auth card
    const authCard = document.querySelector('.auth-card');
    if (authCard) {
        const rotateX = (e.clientY / window.innerHeight - 0.5) * -10;
        const rotateY = (e.clientX / window.innerWidth - 0.5) * 10;
        authCard.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
    }
});

// Flash message auto-dismiss with animation
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(msg => {
        setTimeout(() => {
            msg.style.animation = 'slideOutRight 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55) forwards';
            setTimeout(() => msg.remove(), 500);
        }, 5000);
    });
    
    // Add enter key submit for inputs
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
    
    // Add focus ripple effect
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.style.transition = 'all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)';
        });
    });
});

// Slide out animation for flash messages
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOutRight {
        to {
            opacity: 0;
            transform: translateX(120px) scale(0.9);
        }
    }
`;
document.head.appendChild(style);

// Add button click effect
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('btn-primary') || e.target.classList.contains('glow-btn')) {
        const ripple = document.createElement('span');
        const rect = e.target.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = e.clientX - rect.left - size / 2;
        const y = e.clientY - rect.top - size / 2;
        
        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';
        ripple.classList.add('ripple');
        
        const rippleContainer = e.target.querySelector('.ripple');
        if (rippleContainer) {
            rippleContainer.remove();
        }
        
        e.target.appendChild(ripple);
        
        setTimeout(() => ripple.remove(), 600);
    }
});

// Ripple CSS
const rippleStyle = document.createElement('style');
rippleStyle.textContent = `
    .btn-primary {
        position: relative;
        overflow: hidden;
    }
    
    .ripple {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.5);
        transform: scale(0);
        animation: rippleEffect 0.6s ease-out;
        pointer-events: none;
    }
    
    @keyframes rippleEffect {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
`;
document.head.appendChild(rippleStyle);

// Smooth scroll behavior
document.documentElement.style.scrollBehavior = 'smooth';

// Page transition effect
window.addEventListener('beforeunload', () => {
    document.body.style.opacity = '0';
    document.body.style.transition = 'opacity 0.3s ease';
});

// Loading state for forms
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function(e) {
        const submitBtn = this.querySelector('button[type="submit"]');
        if (submitBtn && !submitBtn.disabled) {
            submitBtn.disabled = true;
            const originalText = submitBtn.textContent;
            submitBtn.innerHTML = '<span class="loading"></span>';
            
            // Re-enable after 5 seconds as fallback
            setTimeout(() => {
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            }, 5000);
        }
    });
});
