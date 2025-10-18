// --- GLOBAL VARIABLES ---
let masterTimeline;

const serviceDetails = {
  residential: {
    title: 'Residential Cleaning',
    content: `<p>Our residential cleaning service is designed to give you the peace of mind you deserve and the time you need to enjoy your life. We offer flexible scheduling for weekly, bi-weekly, or monthly visits.</p><ul><li>Kitchens (counters, floors, appliances)</li><li>Bathrooms (toilets, showers, sinks)</li><li>Living areas (dusting, vacuuming, mopping)</li><li>Bedrooms (making beds, dusting, floors)</li></ul>`
  },
  commercial: {
    title: 'Office Cleaning',
    content: `<p>A clean, professional workspace boosts productivity and creates a welcoming atmosphere for your clients. We provide reliable and efficient cleaning services for offices of all sizes.</p><ul><li>Desk & workstation sanitation</li><li>Restroom cleaning and stocking</li><li>Trash removal and recycling</li><li>Floor care and vacuuming</li><li>Breakroom and kitchen cleaning</li></ul>`
  },
  deep: {
    title: 'Deep Blitz Cleaning',
    content: `<p>Our deep cleaning service is a comprehensive, top-to-bottom clean. It's perfect for a seasonal spring clean or for preparing your home for a special event. We tackle the details that are often overlooked.</p><ul><li>Scrubbing grout and tiles</li><li>Cleaning inside ovens and refrigerators</li><li>Washing baseboards, doors, and window frames</li><li>Detailed dusting including light fixtures and vents</li></ul>`
  },
  tenancy: {
    title: 'Move-in / Move-out Cleaning',
    content: `<p>Specializing in end-of-tenancy cleaning, we work with tenants, landlords, and agencies to ensure properties are immaculate for the next occupants. Our blitz cleaning approach guarantees a fast turnaround without compromising on quality, helping you secure your deposit or prepare your property for rent.</p><ul><li>Full property cleaning to agency standards</li><li>Carpet and upholstery cleaning add-ons</li><li>Guaranteed to pass inspection</li><li>Fast and efficient team for quick turnarounds</li></ul>`
  }
};

// --- NEW REUSABLE PASSWORD VALIDATOR FUNCTION ---
function initializePasswordValidator() {
    const passInput = document.getElementById('register-password');
    if (!passInput) return; // Don't run if the element isn't on the page

    const confirmPassInput = document.getElementById('register-confirm-password');
    const reqs = {
        length: document.getElementById('req-length'),
        upper: document.getElementById('req-upper'),
        lower: document.getElementById('req-lower'),
        num: document.getElementById('req-num'),
        special: document.getElementById('req-special')
    };
    
    const validations = {
        length: val => val.length >= 8,
        upper: val => /[A-Z]/.test(val),
        lower: val => /[a-z]/.test(val),
        num: val => /[0-9]/.test(val),
        special: val => /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(val)
    };

    if (passInput && confirmPassInput) {
        passInput.addEventListener('input', () => {
            const passValue = passInput.value;
            let allValid = true;

            for (const [key, validator] of Object.entries(validations)) {
                const reqItem = reqs[key];
                if (validator(passValue)) {
                    reqItem.classList.add('valid');
                    reqItem.querySelector('i').className = 'fa-solid fa-circle-check';
                } else {
                    reqItem.classList.remove('valid');
                    reqItem.querySelector('i').className = 'fa-solid fa-circle-xmark';
                    allValid = false;
                }
            }
            
            if (allValid) {
                passInput.classList.remove('invalid-input');
                passInput.classList.add('valid-input');
            } else {
                passInput.classList.remove('valid-input');
                passInput.classList.add('invalid-input');
            }
            validateConfirmPassword();
        });

        confirmPassInput.addEventListener('input', validateConfirmPassword);
        
        function validateConfirmPassword() {
            const passValue = passInput.value;
            const confirmValue = confirmPassInput.value;
            
            if (confirmValue.length > 0 && passValue === confirmValue && validations.length(passValue)) {
                passInput.classList.add('valid-input');
                confirmPassInput.classList.add('valid-input');
                passInput.classList.remove('invalid-input');
                confirmPassInput.classList.remove('invalid-input');
                
                if (!confirmPassInput.classList.contains('matched')) {
                     passInput.classList.add('flash-success');
                     confirmPassInput.classList.add('flash-success');
                     setTimeout(() => {
                         passInput.classList.remove('flash-success');
                         confirmPassInput.classList.remove('flash-success');
                     }, 800);
                }
                confirmPassInput.classList.add('matched');

            } else if (confirmValue.length > 0) {
                confirmPassInput.classList.add('invalid-input');
                confirmPassInput.classList.remove('valid-input');
                confirmPassInput.classList.remove('matched');
            } else {
                confirmPassInput.className = '';
            }
        }
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // --- NEW: Navbar Scroll Logic from NieuwburgSite2 ---
    const header = document.querySelector('.site-header');
    if (header) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 30) {
                header.classList.add('scrolled');
            } else {
                header.classList.remove('scrolled');
            }
        });
    }

  // --- Profile Image Preview ---
  const profileImageInput = document.getElementById('profile_image');
  const profilePreview = document.getElementById('profile-preview');

  if (profileImageInput && profilePreview) {
    profileImageInput.addEventListener('change', function() {
      const file = this.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
          profilePreview.src = e.target.result;
        }
        reader.readAsDataURL(file);
      }
    });
  }

// --- NEW: Connect individual service items to the booking modal ---
    const serviceItemButtons = document.querySelectorAll('.service-item-book-button');
    const bookingModalToOpen = document.getElementById('booking-modal');

    if (bookingModalToOpen && serviceItemButtons.length > 0) {
        // We reuse the existing dataLoaded flag logic from your booking modal to be efficient
        let dataLoaded = !document.getElementById('booking-category-list'); 

        const openModalForServiceItems = (e) => {
            e.preventDefault();
            bookingModalToOpen.classList.add('visible');
            if (!dataLoaded) {
                initBookingModal(); // Your existing function that fetches data
                dataLoaded = true;
            } else {
                renderStep1(); // Your existing function that shows the first step
            }
        };

        serviceItemButtons.forEach(btn => {
            btn.addEventListener('click', openModalForServiceItems);
        });
    }

  // --- Profile Dropdown Logic ---
  const profileDropdown = document.getElementById('profile-dropdown');
  if (profileDropdown) {
    const profileBtn = document.getElementById('profile-btn');
    profileBtn.addEventListener('click', () => {
      profileDropdown.classList.toggle('open');
    });
    // Close dropdown if clicking outside
    window.addEventListener('click', function(e) {
      if (!profileDropdown.contains(e.target)) {
        profileDropdown.classList.remove('open');
      }
    });
  }

  // --- NEW: Booking Modal Logic (CORRECTED) ---
const bookingModal = document.getElementById('booking-modal');
if (bookingModal) {
    const openButtons = ['dashboard-quote-btn', 'quote-button', 'hero-book-btn', 'final-cta-btn'];
    const closeButton = document.getElementById('close-booking-modal-button');
    let dataLoaded = false;

    // This function now just opens the modal and calls renderStep1
    const openBookingModal = (e) => {
        e.preventDefault();
        bookingModal.classList.add('visible');
        if (!dataLoaded) {
            initBookingModal(); // Fetches data and sets up listeners ONCE
            dataLoaded = true;
        } else {
            renderStep1(); // Just show step 1 if data is already loaded
        }
    };
    
    const closeBookingModal = () => {
        bookingModal.classList.remove('visible');
    };

    openButtons.forEach(id => {
        const btn = document.getElementById(id);
        if (btn) btn.addEventListener('click', openBookingModal);
    });

    if (closeButton) closeButton.addEventListener('click', closeBookingModal);
    bookingModal.addEventListener('click', (e) => {
        if (e.target === bookingModal) closeBookingModal();
    });
}

  // --- NEW: Typed.js Hero Animation ---
  if (document.getElementById('typed-text')) {
    const typed = new Typed('#typed-text', {
      strings: ['Homes.', 'Offices.', 'End of Tenancy.', 'Post-Construction.'],
      typeSpeed: 70,
      backSpeed: 50,
      loop: true,
      backDelay: 2000,
    });
  }

  // --- NEW: Service Tile Backgrounds ---
  const serviceTiles = document.querySelectorAll('.service-tile');
  if (serviceTiles) {
      const serviceImages = {
          residential: 'Residential.jpg',
          commercial: 'Commercial.jpg',
          deep: 'DeepClean.jpg',
          tenancy: 'End_of_tenancy.jpg'
      };
      serviceTiles.forEach(tile => {
          const service = tile.dataset.service;
          const imageName = serviceImages[service] || 'default_image.jpg';
          tile.style.backgroundImage = `url(/static/img/${imageName})`;
      });
  }

  // --- Reusable Modal Logic ---
  const setupModal = (modalId, openButtonIds, closeButtonId, formId, submissionHandler) => {
    const modal = document.getElementById(modalId);
    if (!modal) return;

    const attachFormListeners = () => {
        const form = document.getElementById(formId);
        if (form && submissionHandler) {
            form.removeEventListener('submit', submissionHandler);
            form.addEventListener('submit', submissionHandler);
            if (formId === 'quote-form') {
                const propType = document.getElementById('property-type');
                const freq = document.getElementById('service-frequency');
                if(propType) propType.addEventListener('change', handlePropertyTypeChange);
                if(freq) freq.addEventListener('change', handleFrequencyChange);
            }
        }
    };

    function openModal(e) {
      if (e) e.preventDefault();
      modal.classList.add('visible');
      attachFormListeners();
    }

    function closeModal() {
      modal.classList.remove('visible');
    }
    
    openButtonIds.forEach(id => {
      const button = document.getElementById(id);
      if(button) button.addEventListener('click', openModal);
    });

    const closeButton = document.getElementById(closeButtonId);
    if (closeButton) closeButton.addEventListener('click', closeModal);

    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeModal();
    });

    attachFormListeners();
  };

  // --- Initialize Modals ---
setupModal('contact-modal', ['contact-nav-link', 'hero-contact-btn', 'contact-footer-btn'], 'close-contact-modal-button', 'contact-form', handleContactFormSubmit);
setupModal('join-team-modal', ['join-team-footer-btn', 'hero-join-team-btn'], 'close-join-team-modal-button', 'staff-application-form', handleStaffApplicationSubmit);

  // --- Service Detail Modal Logic ---
  const serviceModal = document.getElementById('service-detail-modal');
  const closeServiceModalButton = document.getElementById('close-service-modal-button');
  const serviceModalTitle = document.getElementById('service-modal-title');
  const serviceModalContent = document.getElementById('service-modal-content');
  const servicesGrid = document.querySelector('.services-grid');

  if (servicesGrid) {
    servicesGrid.addEventListener('click', (e) => {
      const tile = e.target.closest('.service-tile');
      if (!tile) return;
      const serviceKey = tile.dataset.service;
      const details = serviceDetails[serviceKey];
      if (details && serviceModal) {
        if (serviceModalTitle) serviceModalTitle.textContent = details.title;
        if (serviceModalContent) serviceModalContent.innerHTML = details.content;
        serviceModal.classList.add('visible');
      }
    });
  }

  const closeServiceModal = () => {
    if (serviceModal) serviceModal.classList.remove('visible');
  };

  if (closeServiceModalButton) closeServiceModalButton.addEventListener('click', closeServiceModal);
  if (serviceModal) serviceModal.addEventListener('click', (e) => {
      if (e.target === serviceModal) closeServiceModal();
  });

  // --- FAQ Accordion Logic ---
  const faqQuestions = document.querySelectorAll('.faq-question');
  faqQuestions.forEach(question => {
    question.addEventListener('click', () => {
      const answer = question.nextElementSibling;
      const isActive = question.classList.contains('active');
      faqQuestions.forEach(q => {
        if (q !== question) {
          q.classList.remove('active');
          q.nextElementSibling.style.maxHeight = null;
        }
      });
      if (isActive) {
        question.classList.remove('active');
        answer.style.maxHeight = null;
      } else {
        question.classList.add('active');
        answer.style.maxHeight = answer.scrollHeight + "px";
      }
    });
  });
  


// --- Smooth Scroll for Homepage Links ---
document.querySelectorAll('a[href^="/#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      if (window.location.pathname === '/') {
        e.preventDefault();
        let targetId = this.getAttribute('href').substring(2);
        let targetElement = document.getElementById(targetId);

        if (targetElement) {
            gsap.to(window, {
                duration: 1,
                scrollTo: {
                    y: targetElement,
                    offsetY: 0
                },
                ease: "power2.inOut"
            });
        }
      }
    });
});
  
  // --- Testimonial Slider Logic (Updated with Dynamic Height) ---
  const testimonialSlider = document.querySelector('.testimonial-slider');
  if (testimonialSlider) {
    const testimonials = document.querySelectorAll('.testimonial-card');
    const dotsContainer = document.querySelector('.testimonial-dots');
    const dots = document.querySelectorAll('.dot');
    let currentTestimonial = 0;
    let slideInterval;

    function updateDots(index) {
        dots.forEach(dot => dot.classList.remove('active'));
        dots[index].classList.add('active');
    }

    function showTestimonial(index) {
      // Show the correct card
      testimonials.forEach(testimonial => testimonial.classList.remove('active'));
      testimonials[index].classList.add('active');
      
      // ** THIS IS THE FIX **
      // Measure the height of the newly active card and set the container's height
      const activeCardHeight = testimonials[index].offsetHeight;
      testimonialSlider.style.height = `${activeCardHeight}px`;

      // Update the dots
      updateDots(index);
    }

    function nextTestimonial() {
      currentTestimonial = (currentTestimonial + 1) % testimonials.length;
      showTestimonial(currentTestimonial);
    }
    
    function startSlider() {
      clearInterval(slideInterval);
      slideInterval = setInterval(nextTestimonial, 8000); 
    }

    // --- Event Listeners ---

    if (dotsContainer) {
        dotsContainer.addEventListener('click', (e) => {
            if (e.target.matches('.dot')) {
                const index = parseInt(e.target.dataset.index, 10);
                currentTestimonial = index;
                showTestimonial(currentTestimonial);
                startSlider(); 
            }
        });
    }

    testimonialSlider.addEventListener('mouseenter', () => {
        clearInterval(slideInterval);
    });

    testimonialSlider.addEventListener('mouseleave', () => {
        startSlider();
    });
    
    // Set the initial height of the container when the page first loads
    showTestimonial(currentTestimonial);
    // Start the automatic shuffling
    startSlider(); 
  }

  // --- NEW: Account Deletion Logic ---
  const deleteBtn = document.getElementById('delete-profile-btn');
  const deleteModal = document.getElementById('delete-confirm-modal');
  const closeDeleteModalBtn = document.getElementById('close-delete-modal-button');
  const cancelDeleteBtn = document.getElementById('cancel-delete-btn');
  const confirmDeleteBtn = document.getElementById('confirm-delete-btn');

  if (deleteBtn && deleteModal && confirmDeleteBtn) {
    deleteBtn.addEventListener('click', (e) => {
      e.preventDefault();
      deleteModal.classList.add('visible');
    });

    confirmDeleteBtn.addEventListener('click', async () => {
      try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        
        const response = await fetch('/delete_account', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
          }
        });
        
        const result = await response.json();

        if (result.status === 'ok') {
          const completionModal = document.getElementById('deletion-complete-modal');
          if (completionModal) {
            closeDeleteModal();
            completionModal.classList.add('visible');
            
            const closeCompletionModal = () => {
              completionModal.classList.remove('visible');
              setTimeout(() => { window.location.href = '/'; }, 400);
            };

            const redirectTimeout = setTimeout(closeCompletionModal, 5000);

            const handleOutsideClick = (e) => {
              if (e.target === completionModal) {
                clearTimeout(redirectTimeout);
                closeCompletionModal();
                completionModal.removeEventListener('click', handleOutsideClick);
              }
            };

            completionModal.addEventListener('click', handleOutsideClick);
          }
        } else {
          alert('Deletion failed: ' + (result.message || 'Unknown error.'));
          closeDeleteModal();
        }
      } catch (error) {
        console.error('Deletion error:', error);
        alert('An error occurred. Could not delete account.');
      }
    });

    const closeDeleteModal = () => {
      deleteModal.classList.remove('visible');
    };
    
    if (closeDeleteModalBtn) closeDeleteModalBtn.addEventListener('click', closeDeleteModal);
    if (cancelDeleteBtn) cancelDeleteBtn.addEventListener('click', closeDeleteModal);
    
    deleteModal.addEventListener('click', (e) => {
      if (e.target === deleteModal) closeDeleteModal();
    });
  }

  // --- NEW: Auth Modal and Password Validation ---
    const authModal = document.getElementById('auth-modal');
    if (authModal) {
        const openBtn = document.getElementById('login-nav-btn');
        const closeBtn = document.getElementById('close-auth-modal-button');
        const tabLinks = document.querySelectorAll('.auth-tab-link');
        const forms = document.querySelectorAll('.auth-form-modal');
        const switchToRegister = document.querySelector('.switch-to-register');
        const switchToLogin = document.querySelector('.switch-to-login');

    async function handleLoginSubmit(e) {
    e.preventDefault();
    const form = e.target;
    const errorMessageDiv = document.getElementById('login-error-message');
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    errorMessageDiv.style.display = 'none';

    try {
        const response = await fetch(form.action, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': data.csrf_token
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (response.ok) {
            window.location.href = result.redirect;
        } else {
            errorMessageDiv.className = 'flash error';
            
            if (result.status === 'locked') {
                errorMessageDiv.textContent = result.message;

            } else if (result.status === 'unconfirmed') {
                errorMessageDiv.innerHTML = `
                    ${result.message} 
                    <a href="/resend-confirmation/${result.email}" style="font-weight: bold; color: #721c24; text-decoration: underline;">
                        Resend Confirmation Email
                    </a>
                `;
            } else {
                // For regular errors like wrong password
                errorMessageDiv.textContent = result.message;
            }
            errorMessageDiv.style.display = 'block';
        }
    } catch (error) {
        console.error('Login error:', error);
        errorMessageDiv.textContent = 'A network error occurred. Please try again.';
        errorMessageDiv.style.display = 'block';
    }
}

async function handleRegisterSubmit(e) {
    e.preventDefault();
    const form = e.target;
    const errorMessageDiv = document.getElementById('register-error-message');
    const successMessageDiv = document.getElementById('login-error-message'); // Reuse login div for success
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    errorMessageDiv.style.display = 'none';
    successMessageDiv.style.display = 'none';

    try {
        const response = await fetch(form.action, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': data.csrf_token
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (response.ok) {
            // Switch to login tab and show success message
            document.querySelector('[data-target-form="login-form-modal"]').click();
            successMessageDiv.textContent = result.message;
            successMessageDiv.style.backgroundColor = '#d4edda'; // Green for success
            successMessageDiv.style.color = '#155724';
            successMessageDiv.style.display = 'block';
        } else {
            errorMessageDiv.textContent = result.message;
            errorMessageDiv.style.display = 'block';
        }
    } catch (error) {
        console.error('Registration error:', error);
        errorMessageDiv.textContent = 'A network error occurred. Please try again.';
        errorMessageDiv.style.display = 'block';
    }
}
        function showForm(targetId) {
        forms.forEach(form => form.classList.remove('active'));
        tabLinks.forEach(tab => tab.classList.remove('active'));
        document.getElementById(targetId).classList.add('active');
        document.querySelector(`[data-target-form="${targetId}"]`).classList.add('active');
    }

    const openModal = () => {
        authModal.classList.add('visible');
        showForm('login-form-modal');
    };
    const closeModal = () => authModal.classList.remove('visible');

    if (openBtn) openBtn.addEventListener('click', openModal);
    if (closeBtn) closeBtn.addEventListener('click', closeModal);
    authModal.addEventListener('click', (e) => {
        if (e.target === authModal) closeModal();
    });

    tabLinks.forEach(tab => {
        tab.addEventListener('click', () => showForm(tab.dataset.targetForm));
    });

    if (switchToRegister) switchToRegister.addEventListener('click', (e) => {
        e.preventDefault();
        showForm('register-form-modal');
    });
    if (switchToLogin) switchToLogin.addEventListener('click', (e) => {
        e.preventDefault();
        showForm('login-form-modal');
    });

    const loginForm = document.getElementById('login-form-modal');
    const registerForm = document.getElementById('register-form-modal');
    
    // Attach listeners now that functions are defined in this scope
    if (loginForm) loginForm.addEventListener('submit', handleLoginSubmit);
    if (registerForm) registerForm.addEventListener('submit', handleRegisterSubmit);
    
    // --- Password Real-time Validation ---
    initializePasswordValidator();
        
    }
    // --- Handle Redirects to Auth Modal ---
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('action') === 'login_from_redirect') {
        const authModal = document.getElementById('auth-modal');
        const openBtn = document.getElementById('login-nav-btn');
        const successMessageDiv = document.getElementById('login-error-message');

        if (authModal && openBtn && successMessageDiv) {
            // Programmatically "click" the main login button to open the modal
            openBtn.click(); 

            // Find the success message that Flask rendered on the main page
            const mainFlashMessage = document.querySelector('.flash.success');
            if (mainFlashMessage) {
                // Move the message text into the modal
                successMessageDiv.textContent = mainFlashMessage.textContent;
                successMessageDiv.className = 'flash success'; // Apply success styles
                successMessageDiv.style.display = 'block';
                
                // Hide the original message so it doesn't appear in two places
                mainFlashMessage.style.display = 'none'; 
            }
        }

        // Clean the URL to prevent the modal from re-opening if the user refreshes the page
        history.replaceState(null, '', window.location.pathname);
    }
    // --- Specialized Quote Button in Booking Modal ---
    const specializedQuoteBtn = document.getElementById('specialized-quote-btn');
    if (specializedQuoteBtn) {
        specializedQuoteBtn.addEventListener('click', function(e) {
            e.preventDefault();
            // Close the current booking modal
            const bookingModal = document.getElementById('booking-modal');
            if (bookingModal) bookingModal.classList.remove('visible');

            // Open the contact modal
            const contactModal = document.getElementById('contact-modal');
            if (contactModal) contactModal.classList.add('visible');
        });
    }
// --- DYNAMIC BLOG POST LOADER FOR HOMEPAGE ---
  const homeBlogGrid = document.getElementById('home-blog-grid');
  if (homeBlogGrid) {
    async function fetchAndDisplayPosts() {
        try {
            const response = await fetch('/api/posts');
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            const posts = await response.json();

            // Clear any placeholder content
            homeBlogGrid.innerHTML = '';

            // Get only the first 3 posts
            const recentPosts = posts.slice(0, 3);

            if (recentPosts.length === 0) {
                homeBlogGrid.innerHTML = '<p style="text-align:center; grid-column: 1 / -1;">No blog posts available yet.</p>';
                return;
            }

            recentPosts.forEach(post => {
                const postCard = `
                    <a href="/blog/${post.id}" class="blog-card">
                        <div class="blog-card-image">
                            <img src="https://placehold.co/600x400/e5e7eb/333333?text=Article+Image" alt="Blog post image">
                        </div>
                        <div class="blog-card-content">
                            <h3>${post.title}</h3>
                            <p>${post.excerpt}</p>
                            <span class="read-more">Read More →</span>
                        </div>
                    </a>
                `;
                homeBlogGrid.insertAdjacentHTML('beforeend', postCard);
            });

        } catch (error) {
            console.error('Error fetching blog posts:', error);
            homeBlogGrid.innerHTML = '<p style="text-align:center; color: red; grid-column: 1 / -1;">Could not load blog posts.</p>';
        }
    }

    fetchAndDisplayPosts();
  }
// --- Password Visibility Checkbox ---
    const setupPasswordCheckbox = (checkboxId, inputId) => {
        const checkbox = document.getElementById(checkboxId);
        const passwordInput = document.getElementById(inputId);

        if (checkbox && passwordInput) {
            checkbox.addEventListener('change', function () {
                // Change the input type based on checkbox state
                passwordInput.setAttribute('type', this.checked ? 'text' : 'password');
            });
        }
    };

    setupPasswordCheckbox('showLoginPassword', 'login-password');
    setupPasswordCheckbox('showRegisterPassword', 'register-password');
    setupPasswordCheckbox('showConfirmPassword', 'register-confirm-password');
});

// --- FORM HANDLERS ---
async function handleContactFormSubmit(e) {
  e.preventDefault();
  const form = e.target;
  const modal = document.getElementById('contact-modal');
  const modalContent = form.parentElement;
  
  const data = { 
    name: form.name.value, 
    email: form.email.value, 
    phone: form.phone.value, 
    area: form.area.value,
    message: form.message.value 
  };

  try {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    
    const res = await fetch('/api/contact', {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
      },
      body: JSON.stringify(data)
    });

    if (!res.ok) {
        const errorJson = await res.json();
        throw new Error(errorJson.message || 'A server error occurred.');
    }
    
    const json = await res.json();
    
    if (modalContent) {
        modalContent.innerHTML = `
            <button id="close-contact-modal-button" class="modal-close" aria-label="Close contact form">&times;</button>
            <p style="text-align: center; font-size: 1.1rem; color: var(--accent); padding: 40px 0;">${json.message}</p>
        `;
        const newCloseButton = modalContent.querySelector('#close-contact-modal-button');
        if (newCloseButton && modal) {
            newCloseButton.addEventListener('click', () => modal.classList.remove('visible'));
        }
    }
  } catch (error) {
     console.error("Contact form submission error:", error);
     if (modalContent) {
        modalContent.innerHTML = `
            <button id="close-contact-modal-button" class="modal-close" aria-label="Close contact form">&times;</button>
            <p style="text-align: center; font-size: 1.1rem; color: #c82333; padding: 40px 0;">
                <strong>Error:</strong> Could not send message. Please try again later.
            </p>
        `;
        const newCloseButton = modalContent.querySelector('#close-contact-modal-button');
        if (newCloseButton && modal) {
            newCloseButton.addEventListener('click', () => modal.classList.remove('visible'));
        }
     }
  }
}

async function handleQuoteFormSubmit(e) {
  e.preventDefault();
  const form = e.target;
  
  const formData = new FormData(form);
  const data = {};
  const addons = [];
  for (let [key, value] of formData.entries()) {
      if (key === 'addons') {
          addons.push(value);
      } else {
          data[key] = value;
      }
  }
  data.addons = addons;

  try {
      const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
      const res = await fetch('/api/quote', {
          method: 'POST',
          headers: { 
              'Content-Type': 'application/json',
              'X-CSRFToken': csrfToken
          },
          body: JSON.stringify(data)
      });
      const json = await res.json();

      if (res.ok) {
        location.reload();
      } else {
        alert(json.message || 'An error occurred. Please try again.');
      }
  } catch (error) {
      console.error("Quote form submission error:", error);
      alert('A network error occurred. Please try again.');
  }
}

async function initializePaystack(bookingData) {
    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        const response = await fetch('/initialize-payment', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(bookingData)
        });
        const paymentData = await response.json();

        if (paymentData.authorization_url) {
            const handler = PaystackPop.setup({
                key: 'pk_test_8aeed7ae6e10339f657b2f986288333b5db779a3', // Your public key
                email: bookingData.email,
                amount: bookingData.totalPrice * 100,
                currency: 'ZAR',
                ref: paymentData.reference,
                callback: function(response) {
                    window.location.href = '/payment-callback?reference=' + response.reference;
                },
                onClose: function() {
                    alert('Payment window closed.');
                }
            });
            handler.openIframe();
        } else {
            alert('Could not initialize payment. Please try again.');
        }
    } catch (error) {
        console.error('Paystack initialization error:', error);
        alert('An error occurred setting up payment.');
    }
}

async function handleStaffApplicationSubmit(e) {
    e.preventDefault();
    const form = e.target;
    const modal = document.getElementById('join-team-modal');
    const modalContent = form.parentElement;

    // Use FormData to handle file uploads
    const formData = new FormData(form);

    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        const res = await fetch('/api/staff_apply', {
            method: 'POST',
            headers: {
                // IMPORTANT: Do NOT set Content-Type header. The browser does it for you with FormData.
                'X-CSRFToken': csrfToken
            },
            body: formData // Send the FormData object directly
        });
        const json = await res.json();

        if (modalContent) {
            modalContent.innerHTML = `
                <button id="close-join-team-modal-button" class="modal-close" aria-label="Close form">&times;</button>
                <p style="text-align: center; font-size: 1.1rem; color: var(--accent); padding: 40px 0;">${json.message}</p>
            `;
            const newCloseButton = modalContent.querySelector('#close-join-team-modal-button');
            if (newCloseButton && modal) {
                newCloseButton.addEventListener('click', () => modal.classList.remove('visible'));
            }
        }
    } catch (error) {
        console.error("Staff application submission error:", error);
        alert('An unexpected error occurred. Please try again.');
    }
}

// --- QUOTE FORM CONDITIONAL LOGIC ---
function handlePropertyTypeChange(e) {
  const value = e.target.value;
  const residentialDetails = document.getElementById('residential-details');
  const commercialDetails = document.getElementById('commercial-details');
  if (!residentialDetails || !commercialDetails) return;

  if (value === 'Residential') {
    residentialDetails.classList.remove('hidden');
    commercialDetails.classList.add('hidden');
  } else if (value === 'Commercial' || value === 'Industrial' || value === 'Body Corporate') {
    residentialDetails.classList.add('hidden');
    commercialDetails.classList.remove('hidden');
  } else {
    residentialDetails.classList.add('hidden');
    commercialDetails.classList.add('hidden');
  }
}

function handleFrequencyChange(e) {
  const value = e.target.value;
  const recurringOptions = document.getElementById('recurring-options');
  if (!recurringOptions) return;

  if (value === 'Recurring') {
    recurringOptions.classList.remove('hidden');
  } else {
    recurringOptions.classList.add('hidden');
  }
}

// --- BOOKING CALCULATOR ---
let allServicesData = [];
let selectedCategoryId = null;
let mapInitialized = false;
let selectedAddress = "";

async function initBookingModal() {
    // This listener is now set up ONCE when the modal initializes
    document.querySelectorAll('.booking-back-btn').forEach(btn => {
        btn.onclick = (e) => {
            const targetStep = parseInt(e.target.dataset.targetStep);
            if (targetStep === 1) renderStep1();
            if (targetStep === 2) renderStep2_Address();
        };
    });

    try {
        const response = await fetch('/api/services');
        if (!response.ok) throw new Error('Failed to fetch services');
        allServicesData = await response.json();
        renderStep1();
    } catch (error) {
        // ... error handling
    }
}

// Function to switch between modal steps
function showBookingStep(stepNumber) {
    document.getElementById('booking-step-1').classList.add('hidden');
    document.getElementById('booking-step-2-address').classList.add('hidden');
    document.getElementById('booking-step-3-details').classList.add('hidden');
    document.getElementById('booking-step-4-confirm').classList.add('hidden'); // Add this line

    if (stepNumber === 1) {
        document.getElementById('booking-step-1').classList.remove('hidden');
    } else if (stepNumber === 2) {
        document.getElementById('booking-step-2-address').classList.remove('hidden');
    } else if (stepNumber === 3) {
        document.getElementById('booking-step-3-details').classList.remove('hidden');
    } else if (stepNumber === 4) { // Add this block
        document.getElementById('booking-step-4-confirm').classList.remove('hidden');
    }
}

// --- STEP 1: RENDER CATEGORY SELECTION ---
function renderStep1() {
    showBookingStep(1);
    const categoryListContainer = document.getElementById('booking-category-list');
    
    if (allServicesData.length === 0) {
        categoryListContainer.innerHTML = '<p style="text-align: center;">No services are currently available.</p>';
        return;
    }

    const categoryIcons = {
        'General Cleaning': 'fa-solid fa-house',
        'Exterior Cleaning': 'fa-solid fa-house-chimney-window',
        'End of Tenancy/Pre tenancy': 'fa-solid fa-key',
        'Windows Interior/exterior': 'fa-solid fa-swatchbook',
        'default': 'fa-solid fa-star'
    };

    categoryListContainer.innerHTML = allServicesData.map(category => {
        const iconClass = categoryIcons[category.name] || categoryIcons['default'];
        return `
            <div class="service-category-item" data-category-id="${category.id}">
                <div class="service-category-icon-wrapper"><i class="${iconClass}"></i></div>
                <div class="service-category-text">
                    <h4>${category.name}</h4>
                    <p>${category.description || ''}</p>
                </div>
            </div>
        `;
    }).join('');

    document.querySelectorAll('.service-category-item').forEach(item => {
        item.addEventListener('click', () => {
            selectedCategoryId = item.dataset.categoryId;
            renderStep2_Address();
        });
    });
}

// --- STEP 2: RENDER ADDRESS & MAP ---
function renderStep2_Address() {
    showBookingStep(2);
    document.getElementById('booking-address-next-btn').onclick = () => {
        const streetAddressInput = document.getElementById('street-address');
        if (!streetAddressInput.value) {
            alert('Please enter a service address to continue.');
            return;
        }
        selectedAddress = streetAddressInput.value; // Save the address
        renderStep3_Details();
    };
}
// --- STEP 3: RENDER SERVICE DETAILS & SCHEDULER ---
function renderStep3_Details() {
    showBookingStep(3);
    const titleEl = document.getElementById('booking-step-3-title');
    const calculatorContent = document.getElementById('booking-calculator-content');
    const summaryContainer = document.getElementById('booking-summary-container');

    const addressDisplayText = document.getElementById('address-display-text');
    if (addressDisplayText) addressDisplayText.textContent = selectedAddress;

    const category = allServicesData.find(c => c.id == selectedCategoryId);
    if (!category) return;

    summaryContainer.classList.remove('hidden');
    titleEl.textContent = `Configure: ${category.name}`;

    let formHtml = '<form id="booking-calculator-form" class="booking-calculator-form">';
    formHtml += `
        <div class="booking-category">
            <h3>Select Frequency</h3>
            <div id="booking-frequency-selector" class="frequency-selector">
                <button type="button" class="freq-btn active" data-value="Once-Off">Once-Off</button>
                <button type="button" class="freq-btn" data-value="Weekly">Weekly</button>
                <button type="button" class="freq-btn" data-value="Bi-Weekly">Bi-Weekly</button>
                <button type="button" class="freq-btn" data-value="Monthly">Monthly</button>
            </div>
            <input type="hidden" id="booking-frequency" name="frequency" value="Once-Off">
        </div>
    `;

    category.items.forEach(item => {
        formHtml += `<div class="booking-item-row" data-item-id="${item.id}">`;
        formHtml += `<label for="item-${item.id}" class="booking-item-label">${item.name}</label>`;
        if (category.calculation_method === 'quantity') {
            formHtml += `
                <div class="quantity-selector">
                    <button type="button" class="quantity-btn minus" aria-label="Decrease quantity">-</button>
                    <input type="number" id="item-${item.id}" name="item_${item.id}" class="quantity-input" min="0" value="0" data-item-type="quantity" readonly>
                    <button type="button" class="quantity-btn plus" aria-label="Increase quantity">+</button>
                </div>
            `;
        } else if (category.calculation_method === 'options') {
            formHtml += `<label class="option-selector-label"><input type="checkbox" id="item-${item.id}" name="item_${item.id}" data-item-type="option"><span class="custom-checkbox"></span></label>`;
        }
        formHtml += `</div>`;
    });
    formHtml += '</form>';
    calculatorContent.innerHTML = formHtml;

    attachCalculationAndSubmissionLogic(category);
}

function attachCalculationAndSubmissionLogic(category) {
    // --- Get references to all necessary elements ONCE ---
    const form = document.getElementById('booking-calculator-form');
    const priceTotalEl = document.getElementById('booking-price-total');
    const timeTotalEl = document.getElementById('booking-time-total');
    const hiddenFrequencyInput = document.getElementById('booking-frequency');
    const nextStepBtn = document.getElementById('booking-next-step-btn');
    const confirmBtn = document.getElementById('booking-confirm-btn');
    const dateInput = document.getElementById('booking-date');
    const timeSelect = document.getElementById('booking-time');

    // This object will hold all our booking data as we build it.
    let bookingData = {};

    let totalPrice = 0;
    let totalTime = 0;

    const calculateTotal = () => {
        totalPrice = 0;
        totalTime = 0;
        const selectedFrequency = hiddenFrequencyInput.value;
        const inputs = form.querySelectorAll('input[data-item-type]');
        
        inputs.forEach(input => {
            const row = input.closest('.booking-item-row');
            if (!row) return; // Defensive check
            const itemId = row.dataset.itemId;
            const item = category.items.find(i => i.id == itemId);
            if (!item) return;

            const priceInfo = item.prices.find(p => p.frequency === selectedFrequency);
            if (priceInfo) {
                if (input.type === 'number' && input.value > 0) {
                    totalPrice += input.value * priceInfo.price;
                    totalTime += input.value * item.estimated_time_mins;
                } else if (input.type === 'checkbox' && input.checked) {
                    totalPrice += priceInfo.price;
                    totalTime += item.estimated_time_mins;
                }
            }
        });
        priceTotalEl.textContent = `R${totalPrice.toFixed(2)}`;
        timeTotalEl.textContent = `${totalTime} mins`;
    };
    
    // --- Attach all event listeners for the calculation part ---
    form.addEventListener('change', calculateTotal);
    calculateTotal(); // Initial calculation

    form.querySelectorAll('.quantity-selector').forEach(selector => {
        const minusBtn = selector.querySelector('.minus');
        const plusBtn = selector.querySelector('.plus');
        const input = selector.querySelector('.quantity-input');
        minusBtn.addEventListener('click', () => {
            let val = parseInt(input.value);
            if (val > 0) {
                input.value = val - 1;
                input.dispatchEvent(new Event('change', { bubbles: true }));
            }
        });
        plusBtn.addEventListener('click', () => {
            let val = parseInt(input.value);
            input.value = val + 1;
            input.dispatchEvent(new Event('change', { bubbles: true }));
        });
    });

    const frequencySelector = form.querySelector('#booking-frequency-selector');
    if (frequencySelector) {
        frequencySelector.addEventListener('click', (e) => {
            if (e.target.matches('.freq-btn')) {
                frequencySelector.querySelectorAll('.freq-btn').forEach(btn => btn.classList.remove('active'));
                e.target.classList.add('active');
                hiddenFrequencyInput.value = e.target.dataset.value;
                hiddenFrequencyInput.dispatchEvent(new Event('change', { bubbles: true }));
            }
        });
    }
    hiddenFrequencyInput.addEventListener('change', calculateTotal);

    // --- BUTTON AND SCHEDULER LOGIC ---
    dateInput.min = new Date().toISOString().split("T")[0];

    // CORRECTED LOGIC FOR "Next: Confirm Details" button
    nextStepBtn.onclick = () => {
        // Step 1: Gather service details from the visible form.
        const formData = new FormData(form);
        const services = [];
        for (let [key, value] of formData.entries()) {
            const inputElement = form.querySelector(`#${key.replace(/([\[\]])/g, '\\$1')}`);
            if (key.startsWith('item_') && inputElement && (value > 0 || (inputElement.type === 'checkbox' && inputElement.checked))) {
                const itemId = key.split('_')[1];
                const item = category.items.find(i => i.id == itemId);
                if (item) services.push({ name: item.name, quantity: value });
            }
        }
        
        // Step 2: Store the data in our persistent object.
        bookingData = {
            totalPrice: totalPrice,
            totalTime: totalTime,
            services: services,
            categoryName: category.name,
            frequency: hiddenFrequencyInput.value
        };
        
        // Step 3: Move to the next step.
        showBookingStep(4); 
    };

    dateInput.onchange = async () => {
        const selectedDate = dateInput.value;
        if (!selectedDate) return;
        
        timeSelect.disabled = true;
        timeSelect.innerHTML = '<option>Loading times...</option>';

        try {
            const response = await fetch(`/api/availability/${selectedDate}`);
            if (!response.ok) throw new Error('Failed to fetch times');
            
            const availableSlots = await response.json();
            
            if (availableSlots.length > 0) {
                timeSelect.innerHTML = availableSlots.map(slot => `<option value="${slot}">${slot}</option>`).join('');
                timeSelect.disabled = false;
            } else {
                timeSelect.innerHTML = '<option>No available times on this date</option>';
            }
        } catch (error) {
            console.error("Error fetching availability:", error);
            timeSelect.innerHTML = '<option>Could not load times</option>';
        }
    };
    
    // LOGIC for "Confirm & Proceed to Payment" button
    confirmBtn.onclick = async () => {
        // Step 1: Gather contact details from the current form.
        const customerName = document.getElementById('customer-name').value;
        const customerEmail = document.getElementById('customer-email').value;
        const customerPhone = document.getElementById('customer-phone').value;
        const bookingDate = dateInput.value;
        const bookingTime = timeSelect.value;
        
        if (!customerName || !customerEmail || !customerPhone || !bookingDate || !bookingTime || bookingTime.includes('date first')) {
            alert('Please fill in all your details and select a valid date and time.');
            return;
        }

        // Step 2: Add the contact details to our existing data object.
        bookingData.name = customerName;
        bookingData.email = customerEmail;
        bookingData.phone = customerPhone;
        bookingData.address = selectedAddress;
        bookingData.date = bookingDate;
        bookingData.time = bookingTime;
        
        // Step 3: Proceed to payment with the complete data object.
        initializePaystack(bookingData);
    };
}

// --- GOOGLE MAPS FUNCTIONALITY ---
let map;
let marker;
let autocomplete;

function initMap() {
    if (mapInitialized) {
        return;
    }
    mapInitialized = true;
    initBookingModal(); // Initialize the booking system ONLY AFTER the map is ready.

    if (!document.getElementById("map")) return;

    const capeTown = { lat: -33.9249, lng: 18.4241 };
    map = new google.maps.Map(document.getElementById("map"), {
        zoom: 12,
        center: capeTown,
        mapTypeControl: false,
        streetViewControl: false,
    });
    marker = new google.maps.Marker({ map, position: capeTown, draggable: true });
    const streetAddressInput = document.getElementById("street-address");
    autocomplete = new google.maps.places.Autocomplete(streetAddressInput, {
        componentRestrictions: { country: "za" },
        fields: ["address_components", "geometry", "name", "formatted_address"], // Add formatted_address
        types: ["address"],
    });

    autocomplete.addListener("place_changed", () => {
        const place = autocomplete.getPlace();
        if (!place.geometry || !place.geometry.location) return;

        // ** THIS IS THE CHANGE **
        streetAddressInput.value = place.formatted_address; // Use the full formatted address
        
        map.setCenter(place.geometry.location);
        map.setZoom(17);
        marker.setPosition(place.geometry.location);
    });

    marker.addListener('dragend', () => {
        const geocoder = new google.maps.Geocoder();
        geocoder.geocode({ 'location': marker.getPosition() }, (results, status) => {
            if (status === 'OK' && results[0]) {
                // ** THIS IS THE CHANGE **
                streetAddressInput.value = results[0].formatted_address; // Use the full formatted address
            } else { console.error('Geocoder failed due to: ' + status); }
        });
    });
}