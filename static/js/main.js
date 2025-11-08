// Create dreamy particles
function createParticles() {
    const particlesContainer = document.createElement('div');
    particlesContainer.className = 'particles';
    document.body.appendChild(particlesContainer);
    
    for (let i = 0; i < 30; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.animationDelay = Math.random() * 20 + 's';
        particle.style.animationDuration = (15 + Math.random() * 10) + 's';
        
        const colors = ['#E3FDFD', '#FFE6EB', '#E4FBFF', '#CABBE9', '#FFB6B9'];
        particle.style.background = colors[Math.floor(Math.random() * colors.length)];
        
        particlesContainer.appendChild(particle);
    }
}

// Enhanced parallax with 3D depth
document.addEventListener('mousemove', (e) => {
    const moveX = (e.clientX / window.innerWidth - 0.5) * 30;
    const moveY = (e.clientY / window.innerHeight - 0.5) * 30;
    
    // Move orbs with different speeds for depth
    const orbs = document.querySelectorAll('.orb');
    orbs.forEach((orb, index) => {
        const speed = (index + 1) * 0.6;
        const rotateZ = (e.clientX / window.innerWidth - 0.5) * 20;
        orb.style.transform = `translate(${moveX * speed}px, ${moveY * speed}px) rotate(${rotateZ}deg)`;
    });
    
    // 3D tilt for auth card
    const authCard = document.querySelector('.auth-card');
    if (authCard) {
        const rotateX = (e.clientY / window.innerHeight - 0.5) * -15;
        const rotateY = (e.clientX / window.innerWidth - 0.5) * 15;
        authCard.style.transform = `perspective(1500px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
    }
    
    // Parallax for cards
    const cards = document.querySelectorAll('.glass');
    cards.forEach((card, index) => {
        const depth = (index + 1) * 0.3;
        card.style.transform = `translate(${moveX * depth}px, ${moveY * depth}px)`;
    });
});

// Scroll animations (AOS-like)
function initScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, observerOptions);
    
    document.querySelectorAll('.fade-in-scroll').forEach(el => {
        observer.observe(el);
    });
}

// Flash message auto-dismiss with dreamy animation
document.addEventListener('DOMContentLoaded', function() {
    // Create particles
    createParticles();
    
    // Initialize scroll animations
    initScrollAnimations();
    
    // Flash messages
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(msg => {
        setTimeout(() => {
            msg.style.animation = 'slideOutRight 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55) forwards';
            setTimeout(() => msg.remove(), 600);
        }, 5000);
    });
    
    // Enhanced input interactions
    const inputs = document.querySelectorAll('.glass-input');
    inputs.forEach(input => {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && this.tagName.toLowerCase() !== 'textarea') {
                e.preventDefault();
                const form = this.closest('form');
                if (form) form.submit();
            }
        });
        
        // Add glow effect on focus
        input.addEventListener('focus', function() {
            this.style.transition = 'all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1)';
        });
        
        // Floating label effect
        input.addEventListener('input', function() {
            if (this.value.length > 0) {
                this.style.transform = 'translateY(-3px) scale(1.01)';
            } else {
                this.style.transform = 'translateY(0) scale(1)';
            }
        });
    });
});

// Slide out animation for flash messages
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOutRight {
        to {
            opacity: 0;
            transform: translateX(150px) scale(0.8) rotateZ(10deg);
        }
    }
`;
document.head.appendChild(style);

// Enhanced button click ripple effect
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('btn-primary') || e.target.classList.contains('glow-btn')) {
        const button = e.target;
        const ripple = document.createElement('span');
        const rect = button.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height) * 2;
        const x = e.clientX - rect.left - size / 2;
        const y = e.clientY - rect.top - size / 2;
        
        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';
        ripple.classList.add('ripple');
        
        const existingRipple = button.querySelector('.ripple');
        if (existingRipple) {
            existingRipple.remove();
        }
        
        button.appendChild(ripple);
        
        setTimeout(() => ripple.remove(), 800);
    }
});

// Ripple CSS with dreamy effect
const rippleStyle = document.createElement('style');
rippleStyle.textContent = `
    .btn-primary {
        position: relative;
        overflow: hidden;
    }
    
    .ripple {
        position: absolute;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(255, 255, 255, 0.8), rgba(227, 253, 253, 0.4));
        transform: scale(0);
        animation: rippleEffect 0.8s ease-out;
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

// Page transition effect with pastel glow
window.addEventListener('beforeunload', () => {
    document.body.style.opacity = '0';
    document.body.style.transition = 'opacity 0.4s ease';
    document.body.style.filter = 'blur(10px)';
});

// Loading state for forms with dreamy animation
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function(e) {
        const submitBtn = this.querySelector('button[type="submit"]');
        if (submitBtn && !submitBtn.disabled) {
            submitBtn.disabled = true;
            const originalText = submitBtn.textContent;
            submitBtn.innerHTML = '<span class="loading"></span>';
            submitBtn.style.background = 'linear-gradient(135deg, #CABBE9, #E3FDFD)';
            
            // Re-enable after 5 seconds as fallback
            setTimeout(() => {
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
                submitBtn.style.background = '';
            }, 5000);
        }
    });
});

// Add hover glow to interactive elements
document.querySelectorAll('a, button').forEach(el => {
    el.addEventListener('mouseenter', function() {
        this.style.transition = 'all 0.3s ease';
    });
});

// Animated number counter (for dashboard)
function animateNumber(element, target) {
    const duration = 2000;
    const start = 0;
    const increment = target / (duration / 16);
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            element.textContent = target;
            clearInterval(timer);
        } else {
            element.textContent = Math.floor(current);
        }
    }, 16);
}

// Initialize number animations on page load
window.addEventListener('load', () => {
    const animatedNumbers = document.querySelectorAll('.animated-number');
    animatedNumbers.forEach(el => {
        const target = parseInt(el.textContent);
        el.textContent = '0';
        setTimeout(() => animateNumber(el, target), 500);
    });
});

// Add floating animation to cards on scroll
window.addEventListener('scroll', () => {
    const scrolled = window.pageYOffset;
    const cards = document.querySelectorAll('.glass');
    
    cards.forEach((card, index) => {
        const speed = (index + 1) * 0.1;
        card.style.transform = `translateY(${scrolled * speed}px)`;
    });
});
