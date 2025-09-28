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

document.addEventListener('DOMContentLoaded', function() {
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
    const openButtons = ['book-service-btn', 'process-quote-button', 'dashboard-quote-btn', 'quote-button'];
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
setupModal('contact-modal', ['contact-nav-link'], 'close-contact-modal-button', 'contact-form', handleContactFormSubmit);
setupModal('join-team-modal', ['join-team-btn'], 'close-join-team-modal-button', 'staff-application-form', handleStaffApplicationSubmit);
  
  // --- Navbar Scroll Logic ---
  const nav = document.querySelector('.nav');
  const header = document.querySelector('.site-header');
  let lastScrollY = window.scrollY;

  if (nav && header) {
    window.addEventListener('scroll', () => {
      const currentScrollY = window.scrollY;
      const bannerHeight = header.offsetHeight;
      if (currentScrollY > 50) {
        nav.classList.add('nav-scrolled');
      } else {
        nav.classList.remove('nav-scrolled');
      }
      if (currentScrollY > lastScrollY && currentScrollY > bannerHeight) {
        nav.classList.add('nav-hidden');
      } else {
        nav.classList.remove('nav-hidden');
      }
      lastScrollY = currentScrollY <= 0 ? 0 : currentScrollY;
    });
  }
  
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

  // --- Blog Logic ---
  // if (document.querySelector('.page-blog')) {
  //  loadPosts();
  // }
  
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
                ease: "power2.easeOut"
            });
        }
      }
    });
  });

  // --- Vertical Timeline Animation Logic ---
  function initProcessAnimation() {
      const processSection = document.querySelector('#process');
      if (processSection && typeof gsap !== 'undefined') {
          gsap.registerPlugin(ScrollTrigger, ScrollToPlugin);

          const timelineItems = gsap.utils.toArray(".timeline-item-vertical");
          const contentPanels = gsap.utils.toArray(".timeline-content-panel");
          const timelineProgress = document.querySelector(".timeline-progress");
          const timelineCta = document.querySelector('.timeline-cta');

          const masterTimeline = gsap.timeline({
              scrollTrigger: {
                  trigger: "#process",
                  start: "top top",
                  end: "+=4000",
                  pin: true,
                  scrub: 1,
                  anticipatePin: 1
              }
          });

          masterTimeline.to(timelineProgress, {
              height: "100%",
              duration: 4,
              ease: "none"
          }, 0);

          timelineItems.forEach((item, index) => {
              masterTimeline.add(() => {
                  timelineItems.forEach(el => el.classList.remove('active'));
                  item.classList.add('active');
              }, index);
              masterTimeline.to(contentPanels[index], {
                  opacity: 1,
                  duration: 0.5
              }, index);
              if (index < timelineItems.length - 1) {
                  masterTimeline.to(contentPanels[index], {
                      opacity: 0,
                      duration: 0.5
                  }, index + 0.75);
              }
          });

          masterTimeline.to(timelineCta, {
              opacity: 1,
              visibility: "visible",
              duration: 0.5
          }, 3.5);
      }
  }
  initProcessAnimation();
  
  // --- Testimonial Slider Logic ---
  const testimonialSlider = document.querySelector('.testimonial-slider');
  if (testimonialSlider) {
    const testimonials = document.querySelectorAll('.testimonial-card');
    const prevButton = document.getElementById('prev-testimonial');
    const nextButton = document.getElementById('next-testimonial');
    let currentTestimonial = 0;
    let slideInterval;

    function showTestimonial(index) {
      testimonials.forEach((testimonial, i) => {
        testimonial.classList.remove('active');
      });
      testimonials[index].classList.add('active');
    }

    function nextTestimonial() {
      currentTestimonial = (currentTestimonial + 1) % testimonials.length;
      showTestimonial(currentTestimonial);
    }
    
    function prevTestimonial() {
      currentTestimonial = (currentTestimonial - 1 + testimonials.length) % testimonials.length;
      showTestimonial(currentTestimonial);
    }
    
    function startSlider() {
      clearInterval(slideInterval);
      slideInterval = setInterval(nextTestimonial, 8000);
    }

    if (nextButton) {
      nextButton.addEventListener('click', () => {
        nextTestimonial();
        startSlider();
      });
    }
    if (prevButton) {
      prevButton.addEventListener('click', () => {
        prevTestimonial();
        startSlider();
      });
    }
    
    startSlider();
  }
  
  // --- Back to Top Button Logic ---
  const toTopButton = document.getElementById('back-to-top');
  if (toTopButton) {
    window.addEventListener('scroll', () => {
      if (window.scrollY > 200) {
        toTopButton.classList.add('visible');
      } else {
        toTopButton.classList.remove('visible');
      }
    });
    toTopButton.addEventListener('click', (e) => {
      e.preventDefault();
      window.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    });
  }

  // --- NEW: Account Deletion Logic ---
  const deleteBtn = document.getElementById('delete-profile-btn');
  const deleteModal = document.getElementById('delete-confirm-modal');
  const closeDeleteModalBtn = document.getElementById('close-delete-modal-button');
  const cancelDeleteBtn = document.getElementById('cancel-delete-btn');
  const confirmDeleteBtn = document.getElementById('confirm-delete-btn');

  if (deleteBtn && deleteModal && confirmDeleteBtn) {
    // This listener is for the initial "Delete Profile" button on the dashboard.
    // Its only job is to open the confirmation modal.
    deleteBtn.addEventListener('click', (e) => {
      e.preventDefault(); // Prevent any default button behavior
      deleteModal.classList.add('visible');
    });

    // This listener is for the final "Yes, Delete My Account" button inside the modal.
    // This is the only place where the account deletion is triggered.
    // This listener is for the final "Yes, Delete My Account" button inside the modal.
// This is the only place where the account deletion is triggered.
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
        closeDeleteModal(); // Close the confirmation modal first
        completionModal.classList.add('visible'); // Show the final success message
        
        const closeCompletionModal = () => {
          completionModal.classList.remove('visible');
          setTimeout(() => { window.location.href = '/'; }, 400);
        };

        const redirectTimeout = setTimeout(closeCompletionModal, 5000);

        // This is the updated "click outside" listener
        const handleOutsideClick = (e) => {
          console.log("Overlay clicked. Target is:", e.target); // Debugging line
          if (e.target === completionModal) {
            clearTimeout(redirectTimeout);
            closeCompletionModal();
            // IMPORTANT: Remove the listener after it's used
            completionModal.removeEventListener('click', handleOutsideClick);
          }
        };

        completionModal.addEventListener('click', handleOutsideClick);
        console.log("Click-outside listener attached to deletion-complete-modal."); // Debugging line
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

    // --- Listeners to close the confirmation modal without deleting ---
    const closeDeleteModal = () => {
      deleteModal.classList.remove('visible');
    };
    
    if (closeDeleteModalBtn) closeDeleteModalBtn.addEventListener('click', closeDeleteModal);
    if (cancelDeleteBtn) cancelDeleteBtn.addEventListener('click', closeDeleteModal);
    
    deleteModal.addEventListener('click', (e) => {
      if (e.target === deleteModal) closeDeleteModal();
    });
  }
});

// --- FORM HANDLERS ---
async function handleContactFormSubmit(e) {
  e.preventDefault();
  const form = e.target;
  const modal = document.getElementById('contact-modal');
  const modalContent = form.parentElement;
  
  const data = { name: form.name.value, email: form.email.value, message: form.message.value };

  try {
    const res = await fetch('/api/contact', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
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

async function handleStaffApplicationSubmit(e) {
    e.preventDefault();
    const form = e.target;
    const modal = document.getElementById('join-team-modal');
    const modalContent = form.parentElement;

    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        const res = await fetch('/api/staff_apply', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(data)
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

// --- BLOG LOADER ---
async function loadPosts() {
  const container = document.getElementById('posts');
  if (!container) return;
  container.innerHTML = '<p>Loading posts…</p>';
  try {
    const r = await fetch('/api/posts');
    if (!r.ok) throw new Error('Failed to fetch');
    const posts = await r.json();
    container.innerHTML = posts.length ? posts.map(p => `
      <article class="post-card">
        <h3><a href="/blog/${p.id}">${p.title}</a></h3>
        <p>${p.excerpt}</p>
        <time>${p.date}</time>
      </article>
    `).join('') : '<p>No posts found.</p>';
  } catch (e) {
    container.innerHTML = '<p style="color: red;">Failed to load posts.</p>';
    console.error("Blog loading error:", e);
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

    if (stepNumber === 1) {
        document.getElementById('booking-step-1').classList.remove('hidden');
    } else if (stepNumber === 2) {
        document.getElementById('booking-step-2-address').classList.remove('hidden');
    } else if (stepNumber === 3) {
        document.getElementById('booking-step-3-details').classList.remove('hidden');
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
    // The manual initMap() call has been removed.
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
    const form = document.getElementById('booking-calculator-form');
    const priceTotalEl = document.getElementById('booking-price-total');
    const timeTotalEl = document.getElementById('booking-time-total');
    const hiddenFrequencyInput = document.getElementById('booking-frequency');

    let totalPrice = 0;
    let totalTime = 0;

    const calculateTotal = () => {
        totalPrice = 0;
        totalTime = 0;
        const selectedFrequency = hiddenFrequencyInput.value;
        const inputs = form.querySelectorAll('input[data-item-type]');
        
        inputs.forEach(input => {
            const itemId = input.closest('.booking-item-row').dataset.itemId;
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
    
    form.addEventListener('change', calculateTotal);
    calculateTotal();

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

    // --- SCHEDULER & SUBMISSION LOGIC ---
    const nextStepBtn = document.getElementById('booking-next-step-btn');
    const confirmBtn = document.getElementById('booking-confirm-btn');
    const schedulerContent = document.getElementById('booking-scheduler-content');
    const customerDetailsContent = document.getElementById('booking-customer-details');
    const dateInput = document.getElementById('booking-date');
    const timeSelect = document.getElementById('booking-time');
    dateInput.min = new Date().toISOString().split("T")[0];

    nextStepBtn.onclick = () => {
        schedulerContent.classList.remove('hidden');
        customerDetailsContent.classList.remove('hidden');
        nextStepBtn.classList.add('hidden');
        confirmBtn.classList.remove('hidden');
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
    
    confirmBtn.onclick = async () => {
        // --- Gather all data ---
        const customerName = document.getElementById('customer-name').value;
        const customerEmail = document.getElementById('customer-email').value;
        const customerPhone = document.getElementById('customer-phone').value;
        const bookingDate = dateInput.value;
        const bookingTime = timeSelect.value;
        
        // --- Validation ---
        if (!customerName || !customerEmail || !customerPhone || !bookingDate || !bookingTime || bookingTime.includes('date first')) {
            alert('Please fill in all your details and select a valid date and time.');
            return;
        }

        const formData = new FormData(form);
        const services = [];
        for (let [key, value] of formData.entries()) {
            if (key.startsWith('item_') && (value > 0 || (form.querySelector(`#${key}`).type === 'checkbox' && form.querySelector(`#${key}`).checked))) {
                const itemId = key.split('_')[1];
                const item = category.items.find(i => i.id == itemId);
                services.push({ name: item.name, quantity: value });
            }
        }

        const bookingData = {
            name: customerName,
            email: customerEmail,
            phone: customerPhone,
            address: selectedAddress,
            date: bookingDate,
            time: bookingTime,
            totalPrice: totalPrice,
            totalTime: totalTime,
            services: services,
            categoryName: category.name,
            frequency: hiddenFrequencyInput.value
        };

        // --- Initialize Paystack Payment ---
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
                    amount: bookingData.totalPrice * 100, // Amount in kobo
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
            console.error('Booking submission error:', error);
            alert('An error occurred. Please try again.');
        }
    };
}


// --- GOOGLE MAPS FUNCTIONALITY ---
let map;
let marker;
let autocomplete;

// The initMap function is now called by the Google Maps API script's callback
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