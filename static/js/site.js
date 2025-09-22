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

  // --- NEW: Typed.js Hero Animation ---
if (document.getElementById('typed-text')) {
  const typed = new Typed('#typed-text', {
    strings: ['Homes.', 'Offices.', 'End of Tenancy.', 'Post-Construction.'],
    typeSpeed: 70,
    backSpeed: 50,
    loop: true,
    backDelay: 2000,
  });

  // --- NEW: Service Tile Backgrounds ---
const serviceTiles = document.querySelectorAll('.service-tile');
if (serviceTiles) {
    // Create an object to map your services to your new images
    const serviceImages = {
        residential: 'Residential.jpg', // Replace with your residential image
        commercial: 'Commercial.jpg',  // Replace with your commercial image
        deep: 'DeepClean.jpg',         // Replace with your deep clean image
        tenancy: 'End_of_tenancy.jpg'     // Replace with your tenancy image
    };
 
    serviceTiles.forEach(tile => {
        const service = tile.dataset.service;
        // Use the image from the map, or a default if one isn't found
        const imageName = serviceImages[service] || 'default_image.jpg';
        tile.style.backgroundImage = `url(/static/img/${imageName})`;
    });
}

}

  // --- Reusable Modal Logic ---
  const setupModal = (modalId, openButtonIds, closeButtonId, formId, submissionHandler) => {
    const modal = document.getElementById(modalId);
    if (!modal) return;

    // Use a custom event to close the modal to avoid listener conflicts
    modal.addEventListener('close', closeModal);

    const modalContent = modal.querySelector('.modal-content');
    const originalModalHTML = modalContent ? modalContent.innerHTML : '';

    function openModal(e) {
      e.preventDefault();
      modal.classList.add('visible');
    }

    function closeModal() {
      modal.classList.remove('visible');
      setTimeout(() => {
        if (modalContent) {
          modalContent.innerHTML = originalModalHTML;
          // Re-attach listeners after rebuilding HTML
          const newCloseButton = document.getElementById(closeButtonId);
          if (newCloseButton) newCloseButton.addEventListener('click', closeModal);
          
          const newForm = document.getElementById(formId);
          if (newForm && submissionHandler) {
              newForm.addEventListener('submit', submissionHandler);
              // Special handling for quote form's dynamic selects
              if (formId === 'quote-form') {
                  const propType = document.getElementById('property-type');
                  const freq = document.getElementById('service-frequency');
                  if(propType) propType.addEventListener('change', handlePropertyTypeChange);
                  if(freq) freq.addEventListener('change', handleFrequencyChange);
              }
          }
        }
      }, 300); // Match CSS transition time
    }

    openButtonIds.forEach(id => {
      const openButton = document.getElementById(id);
      if (openButton) openButton.addEventListener('click', openModal);
    });

    const closeButton = document.getElementById(closeButtonId);
    if (closeButton) closeButton.addEventListener('click', closeModal);

    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeModal();
    });

    const form = document.getElementById(formId);
    if (form && submissionHandler) {
      form.addEventListener('submit', submissionHandler);
    }
    
    // Attach handlers for quote form if it exists
    if (formId === 'quote-form') {
        const propType = document.getElementById('property-type');
        const freq = document.getElementById('service-frequency');
        if(propType) propType.addEventListener('change', handlePropertyTypeChange);
        if(freq) freq.addEventListener('change', handleFrequencyChange);
    }
  };

  // --- Initialize Modals ---
  setupModal('contact-modal', ['contact-nav-link'], 'close-contact-modal-button', 'contact-form', handleContactFormSubmit);
  setupModal('quote-modal', ['quote-button', 'process-quote-button'], 'close-quote-modal-button', 'quote-form', handleQuoteFormSubmit);
  
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
                    offsetY: 0 // Adjust for your sticky nav
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

  // Initialize the animation when the DOM is ready
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
  
  if (deleteBtn && deleteModal) {
    // Open the confirmation modal
    deleteBtn.addEventListener('click', (e) => {
      e.preventDefault();
      deleteModal.classList.add('visible');
    });

    // Function to close the modal
    const closeDeleteModal = () => {
      deleteModal.classList.remove('visible');
    };
    
    // Attach close event to buttons and overlay
    closeDeleteModalBtn.addEventListener('click', closeDeleteModal);
    cancelDeleteBtn.addEventListener('click', closeDeleteModal);
    deleteModal.addEventListener('click', (e) => {
      if (e.target === deleteModal) closeDeleteModal();
    });

    // Handle the final deletion
confirmDeleteBtn.addEventListener('click', async () => {
  try {
    const csrfToken = '{{ csrf_token() }}'; // This will be rendered by Jinja2
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
      completionModal.classList.add('visible');

      // Function to close the modal and redirect
const closeCompletionModal = () => {
  completionModal.classList.remove('visible');
  // Wait for the 300ms fade-out animation to finish before redirecting
  setTimeout(() => {
    window.location.href = '/'; // Redirect to homepage
  }, 300); 
};

      // Set a timeout to automatically close and redirect
      const redirectTimeout = setTimeout(closeCompletionModal, 8000);

      // Allow clicking the overlay to close it sooner
      completionModal.addEventListener('click', (e) => {
        if (e.target === completionModal) {
          clearTimeout(redirectTimeout); // Stop the automatic redirect
          closeCompletionModal();
        }
      });
    }
  } catch (error) {
    console.error('Deletion error:', error);
    alert('An error occurred. Could not delete account.');
  }
});
  }
});

// --- FORM HANDLERS ---
async function handleContactFormSubmit(e) {
  e.preventDefault();
  const form = e.target;
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
        if (newCloseButton) {
            newCloseButton.addEventListener('click', () => document.getElementById('contact-modal').dispatchEvent(new Event('close')));
        }
    }
    
  } catch (error) {
     console.error("Contact form submission error:", error);
  }
}

async function handleQuoteFormSubmit(e) {
  e.preventDefault();
  const form = e.target;
  const modalContent = form.parentElement;
  
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
      const res = await fetch('/api/quote', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
      });
      const json = await res.json();

      if (modalContent) {
        modalContent.innerHTML = `
            <button id="close-quote-modal-button" class="modal-close" aria-label="Close quote form">&times;</button>
            <p style="text-align: center; font-size: 1.1rem; color: var(--accent); padding: 40px 0;">${json.message}</p>
        `;
        const newCloseButton = modalContent.querySelector('#close-quote-modal-button');
        if (newCloseButton) {
            newCloseButton.addEventListener('click', () => document.getElementById('quote-modal').dispatchEvent(new Event('close')));
        }
      }
  } catch (error) {
      console.error("Quote form submission error:", error);
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