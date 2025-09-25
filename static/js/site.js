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

  // --- NEW: Booking Modal Logic ---
const bookingModal = document.getElementById('booking-modal');
if (bookingModal) {
    const openButtons = ['book-service-btn', 'process-quote-button', 'dashboard-quote-btn', 'quote-button'];
    const closeButton = document.getElementById('close-booking-modal-button');
    let calculatorInitialized = false; // Prevents re-loading data

    const openBookingModal = (e) => {
        e.preventDefault();
        bookingModal.classList.add('visible');
        // Only initialize the calculator the very first time the modal is opened
        if (!calculatorInitialized) {
            initBookingModal();
            calculatorInitialized = true;
        } else {
            // If already initialized, just reset to the first step
            renderStep1();
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
  if (document.querySelector('.page-blog')) {
    loadPosts();
  }
  
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
  initBookingCalculator();
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
let allServicesData = []; // Store service data globally within the script's scope

async function initBookingModal() {
    const step1 = document.getElementById('booking-step-1');
    const categoryListContainer = document.getElementById('booking-category-list');
    if (!step1 || !categoryListContainer) return;

    try {
        // Fetch service data only once
        const response = await fetch('/api/services');
        if (!response.ok) throw new Error('Failed to fetch services');
        allServicesData = await response.json();

        // Render the first step (category selection)
        renderStep1();

    } catch (error) {
        categoryListContainer.innerHTML = '<p style="color: red; text-align: center;">Error loading services. Please try again later.</p>';
        console.error("Booking modal error:", error);
    }
}

function renderStep1() {
    const step1 = document.getElementById('booking-step-1');
    const step2 = document.getElementById('booking-step-2');
    const categoryListContainer = document.getElementById('booking-category-list');
    
    // Reset to step 1 view
    step1.classList.remove('hidden');
    step2.classList.add('hidden');
    document.getElementById('booking-calculator-content').innerHTML = '';
    document.getElementById('booking-scheduler-content').classList.add('hidden');
    document.getElementById('booking-customer-details').classList.add('hidden');
    document.getElementById('booking-summary-container').classList.add('hidden');
    document.getElementById('booking-next-step-btn').classList.remove('hidden');
    document.getElementById('booking-confirm-btn').classList.add('hidden');


    if (allServicesData.length === 0) {
        categoryListContainer.innerHTML = '<p style="text-align: center;">No services are currently available. Please check back later.</p>';
        return;
    }

    // Generate HTML for each service category
    categoryListContainer.innerHTML = allServicesData.map(category => `
        <div class="service-category-item" data-category-id="${category.id}">
            <h4>${category.name}</h4>
            <p>${category.description || ''}</p>
        </div>
    `).join('');

    // Add click listeners to each category item
    document.querySelectorAll('.service-category-item').forEach(item => {
        item.addEventListener('click', () => {
            const categoryId = item.dataset.categoryId;
            renderStep2(categoryId);
        });
    });
}


function renderStep2(categoryId) {
    const step1 = document.getElementById('booking-step-1');
    const step2 = document.getElementById('booking-step-2');
    const titleEl = document.getElementById('booking-step-2-title');
    const calculatorContent = document.getElementById('booking-calculator-content');
    const backBtn = document.getElementById('booking-back-btn');
    const summaryContainer = document.getElementById('booking-summary-container');

    const category = allServicesData.find(c => c.id == categoryId);
    if (!category) return;

    // Switch views
    step1.classList.add('hidden');
    step2.classList.remove('hidden');
    summaryContainer.classList.remove('hidden');
    titleEl.textContent = `Configure: ${category.name}`;

    // Build the form for the selected category's items
    let formHtml = '<form id="booking-calculator-form" class="booking-calculator-form">';
    formHtml += `
        <div class="booking-category">
            <h3>Select Frequency</h3>
            <select id="booking-frequency" name="frequency" class="form-control">
                <option value="Once-Off">Once-Off</option>
                <option value="Weekly">Weekly</option>
                <option value="Bi-Weekly">Bi-Weekly</option>
                <option value="Monthly">Monthly</option>
            </select>
        </div>
    `;

    category.items.forEach(item => {
        formHtml += `<div class="booking-item-row" data-item-id="${item.id}">`;
        if (category.calculation_method === 'quantity') {
            formHtml += `<label for="item-${item.id}">${item.name}</label>`;
            formHtml += `<input type="number" id="item-${item.id}" name="item_${item.id}" class="quantity-input" min="0" value="0" data-item-type="quantity">`;
        } else if (category.calculation_method === 'options') {
            formHtml += `<label for="item-${item.id}">${item.name}</label>`;
            formHtml += `<input type="checkbox" id="item-${item.id}" name="item_${item.id}" data-item-type="option">`;
        }
        formHtml += `</div>`;
    });
    formHtml += '</form>';
    calculatorContent.innerHTML = formHtml;

    // Attach calculation logic
    attachCalculationAndSubmissionLogic(category);

    // Add event listener for the back button
    backBtn.onclick = renderStep1;
}


function attachCalculationAndSubmissionLogic(category) {
    const form = document.getElementById('booking-calculator-form');
    const priceTotalEl = document.getElementById('booking-price-total');
    const timeTotalEl = document.getElementById('booking-time-total');

    const calculateTotal = () => {
        let totalPrice = 0;
        let totalTime = 0;
        const selectedFrequency = document.getElementById('booking-frequency').value;
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
    form.addEventListener('keyup', calculateTotal);
    calculateTotal();

    // --- SCHEDULER & SUBMISSION LOGIC ---
    const nextStepBtn = document.getElementById('booking-next-step-btn');
    const confirmBtn = document.getElementById('booking-confirm-btn');
    const schedulerContent = document.getElementById('booking-scheduler-content');
    const customerDetailsContent = document.getElementById('booking-customer-details');
    const dateInput = document.getElementById('booking-date');
    const timeSelect = document.getElementById('booking-time');

    dateInput.min = new Date().toISOString().split("T")[0];

    // Use .onclick to ensure we're not adding duplicate listeners
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
        timeSelect.innerHTML = '<option>Loading available times...</option>';
        try {
            const response = await fetch(`/api/availability/${selectedDate}`);
            const availableSlots = await response.json();
            if (availableSlots.length > 0) {
                timeSelect.innerHTML = '<option value="">-- Select a time --</option>';
                availableSlots.forEach(slot => {
                    const option = document.createElement('option');
                    option.value = slot;
                    option.textContent = slot;
                    timeSelect.appendChild(option);
                });
                timeSelect.disabled = false;
            } else {
                timeSelect.innerHTML = '<option>No available slots for this day</option>';
            }
        } catch (error) {
            console.error("Error fetching availability:", error);
            timeSelect.innerHTML = '<option>Error loading times</option>';
        }
    };

    confirmBtn.onclick = async () => {
        const selectedFrequency = document.getElementById('booking-frequency').value;
        const selectedDate = dateInput.value;
        const selectedTime = timeSelect.value;
        const customerName = document.getElementById('customer-name').value;
        const customerEmail = document.getElementById('customer-email').value;
        const customerPhone = document.getElementById('customer-phone').value;

        if (!selectedDate || !selectedTime || !customerName || !customerEmail) {
            alert('Please fill in all required fields: date, time, name, and email.');
            return;
        }

        let services = [];
        const inputs = form.querySelectorAll('input[data-item-type]');
        inputs.forEach(input => {
            if ((input.type === 'number' && input.value > 0) || (input.type === 'checkbox' && input.checked)) {
                const row = input.closest('.booking-item-row');
                services.push({
                    id: row.dataset.itemId,
                    name: row.querySelector('label').textContent,
                    quantity: input.type === 'number' ? input.value : 1
                });
            }
        });

        const bookingData = {
            name: customerName, email: customerEmail, phone: customerPhone,
            date: selectedDate, time: selectedTime, frequency: selectedFrequency,
            totalPrice: parseFloat(priceTotalEl.textContent.replace('R', '')),
            totalTime: parseInt(timeTotalEl.textContent),
            services: services
        };

        try {
            confirmBtn.disabled = true;
            confirmBtn.textContent = 'Submitting...';
            
            const response = await fetch('/api/create_booking', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(bookingData)
            });
            const result = await response.json();

            if (result.status === 'ok') {
                const modalContent = document.querySelector('#booking-modal .modal-content');
                modalContent.innerHTML = `
                    <button id="close-booking-modal-button" class="modal-close" aria-label="Close form">&times;</button>
                    <p style="text-align: center; font-size: 1.1rem; color: var(--accent); padding: 40px 0;">${result.message}</p>
                `;
                const newCloseButton = modalContent.querySelector('#close-booking-modal-button');
                newCloseButton.addEventListener('click', () => {
                    document.getElementById('booking-modal').classList.remove('visible');
                    // We might need to reload the page or re-initialize the modal for the next booking
                });
            } else {
                alert('Booking failed: ' + (result.message || 'Unknown error.'));
            }
        } catch (error) {
            console.error('Booking submission error:', error);
            alert('An unexpected network error occurred.');
        } finally {
            confirmBtn.disabled = false;
            confirmBtn.textContent = 'Confirm & Book Now';
        }
    };
}