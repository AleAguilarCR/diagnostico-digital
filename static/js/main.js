// JavaScript principal para la aplicación

// Utilidades generales
const Utils = {
    // Mostrar notificación toast
    showToast: function(message, type = 'info') {
        const toastContainer = document.getElementById('toast-container') || this.createToastContainer();
        const toast = this.createToast(message, type);
        toastContainer.appendChild(toast);
        
        // Mostrar toast
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remover después de que se oculte
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    },
    
    createToastContainer: function() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
        return container;
    },
    
    createToast: function(message, type) {
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.setAttribute('role', 'alert');
        
        const colors = {
            success: 'text-bg-success',
            error: 'text-bg-danger',
            warning: 'text-bg-warning',
            info: 'text-bg-info'
        };
        
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        
        toast.innerHTML = `
            <div class="toast-header ${colors[type] || colors.info}">
                <i class="${icons[type] || icons.info} me-2"></i>
                <strong class="me-auto">Notificación</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;
        
        return toast;
    },
    
    // Validar email
    validateEmail: function(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    },
    
    // Formatear fecha
    formatDate: function(date) {
        return new Intl.DateTimeFormat('es-ES', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }).format(new Date(date));
    },
    
    // Debounce function
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};

// Manejo de formularios
const FormHandler = {
    // Validar formulario de login
    validateLoginForm: function(formData) {
        const errors = [];
        
        if (!formData.email || !Utils.validateEmail(formData.email)) {
            errors.push('Por favor ingrese un correo electrónico válido');
        }
        
        if (!formData.nombre_empresa || formData.nombre_empresa.trim().length < 2) {
            errors.push('El nombre de la empresa debe tener al menos 2 caracteres');
        }
        
        if (!formData.tipo_empresa || formData.tipo_empresa.trim().length < 5) {
            errors.push('Por favor describa el tipo de empresa con más detalle');
        }
        
        return errors;
    },
    
    // Mostrar errores de validación
    showValidationErrors: function(errors) {
        const errorContainer = document.getElementById('validation-errors') || this.createErrorContainer();
        
        if (errors.length > 0) {
            errorContainer.innerHTML = `
                <div class="alert alert-danger alert-dismissible fade show" role="alert">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <strong>Por favor corrija los siguientes errores:</strong>
                    <ul class="mb-0 mt-2">
                        ${errors.map(error => `<li>${error}</li>`).join('')}
                    </ul>
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `;
            errorContainer.scrollIntoView({ behavior: 'smooth' });
        } else {
            errorContainer.innerHTML = '';
        }
    },
    
    createErrorContainer: function() {
        const container = document.createElement('div');
        container.id = 'validation-errors';
        container.className = 'mb-3';
        
        const form = document.querySelector('form');
        if (form) {
            form.insertBefore(container, form.firstChild);
        }
        
        return container;
    }
};

// Manejo de evaluaciones
const EvaluationHandler = {
    // Calcular progreso de evaluación
    calculateProgress: function() {
        const totalQuestions = document.querySelectorAll('.pregunta-container').length;
        const answeredQuestions = document.querySelectorAll('input[type="radio"]:checked').length;
        
        return Math.round((answeredQuestions / totalQuestions) * 100);
    },
    
    // Actualizar barra de progreso
    updateProgressBar: function() {
        const progressBar = document.getElementById('progress-bar');
        if (progressBar) {
            const progress = this.calculateProgress();
            progressBar.style.width = `${progress}%`;
            progressBar.setAttribute('aria-valuenow', progress);
            progressBar.textContent = `${progress}%`;
        }
    },
    
    // Validar que todas las preguntas estén respondidas
    validateAllAnswered: function() {
        const questions = document.querySelectorAll('.pregunta-container');
        const unanswered = [];
        
        questions.forEach((question, index) => {
            const radios = question.querySelectorAll('input[type="radio"]');
            const answered = Array.from(radios).some(radio => radio.checked);
            
            if (!answered) {
                unanswered.push(index + 1);
            }
        });
        
        return unanswered;
    },
    
    // Resaltar preguntas sin responder
    highlightUnanswered: function(unansweredQuestions) {
        // Remover resaltados previos
        document.querySelectorAll('.pregunta-container').forEach(container => {
            container.classList.remove('border-danger', 'bg-light-danger');
        });
        
        // Resaltar preguntas sin responder
        unansweredQuestions.forEach(questionNumber => {
            const container = document.querySelectorAll('.pregunta-container')[questionNumber - 1];
            if (container) {
                container.classList.add('border-danger', 'bg-light-danger');
                container.style.borderWidth = '2px';
            }
        });
        
        // Scroll a la primera pregunta sin responder
        if (unansweredQuestions.length > 0) {
            const firstUnanswered = document.querySelectorAll('.pregunta-container')[unansweredQuestions[0] - 1];
            if (firstUnanswered) {
                firstUnanswered.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
    }
};

// Efectos visuales y animaciones
const VisualEffects = {
    // Animar entrada de elementos
    animateIn: function(elements, delay = 100) {
        elements.forEach((element, index) => {
            element.style.opacity = '0';
            element.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                element.style.transition = 'all 0.5s ease';
                element.style.opacity = '1';
                element.style.transform = 'translateY(0)';
            }, index * delay);
        });
    },
    
    // Efecto de pulso para botones
    pulseButton: function(button) {
        button.classList.add('pulse');
        setTimeout(() => {
            button.classList.remove('pulse');
        }, 600);
    },
    
    // Efecto de carga en botones
    setButtonLoading: function(button, loading = true) {
        if (loading) {
            button.dataset.originalText = button.innerHTML;
            button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Procesando...';
            button.disabled = true;
        } else {
            button.innerHTML = button.dataset.originalText || button.innerHTML;
            button.disabled = false;
        }
    }
};

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function() {
    // Animar elementos al cargar
    const cards = document.querySelectorAll('.card');
    if (cards.length > 0) {
        VisualEffects.animateIn(Array.from(cards));
    }
    
    // Configurar tooltips de Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Configurar popovers de Bootstrap
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Agregar listeners para cambios en formularios de evaluación
    const radioInputs = document.querySelectorAll('input[type="radio"]');
    radioInputs.forEach(input => {
        input.addEventListener('change', function() {
            // Actualizar progreso
            EvaluationHandler.updateProgressBar();
            
            // Remover resaltado de error si existe
            const container = this.closest('.pregunta-container');
            if (container) {
                container.classList.remove('border-danger', 'bg-light-danger');
                container.style.borderWidth = '';
            }
            
            // Efecto visual en la selección
            const label = document.querySelector(`label[for="${this.id}"]`);
            if (label) {
                VisualEffects.pulseButton(label);
            }
        });
    });
    
    // Configurar validación en tiempo real para formularios
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                this.classList.remove('is-invalid');
                if (this.checkValidity()) {
                    this.classList.add('is-valid');
                } else {
                    this.classList.add('is-invalid');
                }
            });
        });
    });
});

// Funciones globales para uso en templates
window.Utils = Utils;
window.FormHandler = FormHandler;
window.EvaluationHandler = EvaluationHandler;
window.VisualEffects = VisualEffects;