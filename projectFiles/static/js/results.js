// Results page JavaScript functionality
// Institution Profiler - Results Page Interactions

// Global variables for image tracking
let loadedImagesCount = 0;
let totalImagesAttempted = 0;

// Toggle functions for UI elements
function toggleBenchmarks() {
    const card = document.getElementById('benchmarks-card');
    const button = event.target.closest('button');
    
    if (card.style.display === 'none') {
        card.style.display = 'block';
        button.innerHTML = '<i class="fas fa-chart-line me-2"></i>Hide Benchmarks';
        // Smooth scroll to the metrics section
        document.getElementById('quality-metrics').scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    } else {
        card.style.display = 'none';
        button.innerHTML = '<i class="fas fa-chart-line me-2"></i>View Benchmarks';
    }
}

function toggleRawData() {
    const rawData = document.getElementById('raw-data');
    if (rawData.style.display === 'none') {
        rawData.style.display = 'block';
    } else {
        rawData.style.display = 'none';
    }
}

// Image loading handlers to update actual counts
function handleImageLoad(img) {
    loadedImagesCount++;
    updateImageCount();
    // Simply remove loading indicator when image loads
    const container = img.closest('[data-image-container], .logo-container, .image-container');
    if (container) {
        container.classList.remove('image-loading');
        container.setAttribute('data-loaded', 'true');
    }
}

function handleImageError(img) {
    const container = img.closest('[data-image-container], .logo-container, .image-container');
    if (container) {
        container.style.display = 'none';
        container.setAttribute('data-failed', 'true');
        container.classList.remove('image-loading');
    }
    updateImageCount();
}

function updateImageCount() {
    const countElement = document.getElementById('images-count');
    if (countElement && totalImagesAttempted > 0) {
        const loadedText = loadedImagesCount > 0 ? `${loadedImagesCount}/${totalImagesAttempted}` : totalImagesAttempted.toString();
        countElement.textContent = loadedText;
        
        // Update the label to show loading status
        const labelElement = countElement.nextElementSibling;
        if (labelElement && totalImagesAttempted > 0) {
            const failedCount = totalImagesAttempted - loadedImagesCount;
            if (failedCount > 0) {
                labelElement.textContent = `Images (${failedCount} failed)`;
            } else {
                labelElement.textContent = 'Images Loaded';
            }
        }
    }
}

// Pre-validate image URLs before display
function preValidateImages() {
    // Handle both data-image-container and other image containers like logos
    const imageContainers = document.querySelectorAll('[data-image-container], .logo-container, .image-container');
    
    imageContainers.forEach((container, index) => {
        const img = container.querySelector('img');
        if (img && img.src) {            // Add loading indicator
            container.classList.add('image-loading');
            
            // Simple timeout - just remove loading indicator after 3 seconds
            // Don't try to determine success/failure, let the actual load/error events handle that
            setTimeout(() => {
                container.classList.remove('image-loading');
            }, 3000); // 3 second timeout - much shorter and simpler
        }
    });
}

// Dynamic Theme Application
function applyInstitutionTheme() {
    const institutionType = document.body.dataset.institutionType || '';
    const root = document.documentElement;
    
    // Remove any existing theme classes
    root.classList.remove('theme-healthcare', 'theme-financial', 'theme-academic', 'theme-corporate', 'theme-government', 'theme-technology');
    
    // Apply theme based on institution type
    if (institutionType.includes('hospital') || institutionType.includes('medical') || institutionType.includes('health')) {
        root.classList.add('theme-healthcare');
    } else if (institutionType.includes('bank') || institutionType.includes('financial') || institutionType.includes('insurance')) {
        root.classList.add('theme-financial');
    } else if (institutionType.includes('university') || institutionType.includes('college') || institutionType.includes('school')) {
        root.classList.add('theme-academic');
    } else if (institutionType.includes('government') || institutionType.includes('federal') || institutionType.includes('municipal')) {
        root.classList.add('theme-government');
    } else if (institutionType.includes('tech') || institutionType.includes('software') || institutionType.includes('it')) {
        root.classList.add('theme-technology');
    } else {
        root.classList.add('theme-corporate');
    }
}

// Update sector-specific icons based on institution type
function updateSectorIcons() {
    const institutionType = document.body.dataset.institutionType || '';
    const iconMappings = {
        'healthcare': {
            'student_population': 'fas fa-user-injured',
            'faculty_count': 'fas fa-user-md',
            'annual_revenue': 'fas fa-heartbeat',
            'patient_capacity': 'fas fa-bed',
            'campus_size': 'fas fa-hospital',
            'employees_worldwide': 'fas fa-stethoscope'
        },
        'financial': {
            'student_population': 'fas fa-users',
            'faculty_count': 'fas fa-user-tie',
            'annual_revenue': 'fas fa-dollar-sign',
            'patient_capacity': 'fas fa-building',
            'campus_size': 'fas fa-landmark',
            'employees_worldwide': 'fas fa-briefcase'
        },
        'academic': {
            'student_population': 'fas fa-graduation-cap',
            'faculty_count': 'fas fa-chalkboard-teacher',
            'annual_revenue': 'fas fa-university',
            'patient_capacity': 'fas fa-users',
            'campus_size': 'fas fa-school',
            'employees_worldwide': 'fas fa-book'
        }
    };
    
    let sectorIcons = iconMappings['academic']; // default
    
    if (institutionType.includes('hospital') || institutionType.includes('medical') || institutionType.includes('health')) {
        sectorIcons = iconMappings['healthcare'];
    } else if (institutionType.includes('bank') || institutionType.includes('financial') || institutionType.includes('insurance')) {
        sectorIcons = iconMappings['financial'];
    }
    
    // Update icons in fact cards
    Object.keys(sectorIcons).forEach(key => {
        const iconElement = document.querySelector(`[data-metric="${key}"] .fact-icon i`);
        if (iconElement) {
            iconElement.className = sectorIcons[key];
        }
    });
}

// Hide empty sections for cleaner display
function hideEmptySections() {
    const contentCards = document.querySelectorAll('.content-card');
    
    contentCards.forEach(section => {
        // Check for leadership cards
        const hasLeadershipCards = section.querySelectorAll('.leadership-card').length > 0 &&
            Array.from(section.querySelectorAll('.leadership-name')).some(el => el.textContent.trim() !== '' && el.textContent.trim() !== 'Unknown');
        
        // Check for fact cards
        const hasFactCards = section.querySelectorAll('.fact-card').length > 0 &&
            Array.from(section.querySelectorAll('.fact-number')).some(el => el.textContent.trim() !== '' && el.textContent.trim() !== 'Unknown');
          // Check for lists with content
        const hasListItems = section.querySelectorAll('.enhanced-list li, .program-item, .affiliation-item, .programs-list li, .services-list li, .specialties-list li, .departments-list li, .degrees-list li, .products-list li').length > 0 &&
            Array.from(section.querySelectorAll('.enhanced-list li, .program-item, .affiliation-item, .programs-list li, .services-list li, .specialties-list li, .departments-list li, .degrees-list li, .products-list li')).some(el => el.textContent.trim() !== '' && el.textContent.trim() !== 'Unknown');
        
        const hasImages = section.querySelectorAll('img:not([style*="display: none"])').length > 0;
        
        const hasInfoItems = section.querySelectorAll('dl dd').length > 0 &&
            Array.from(section.querySelectorAll('dl dd')).some(el => el.textContent.trim() !== '' && el.textContent.trim() !== 'Unknown');        // Check for benchmark items (allow 0 values as they can be legitimate)
        const hasBenchmarkItems = section.querySelectorAll('.benchmark-item').length > 0 &&
            Array.from(section.querySelectorAll('.benchmark-value')).some(el => el.textContent.trim() !== '' && el.textContent.trim() !== 'Unknown');
        
        // Check if section has any meaningful content
        const hasContent = hasLeadershipCards || hasFactCards || hasListItems || hasImages || hasInfoItems || hasBenchmarkItems;
        
        if (!hasContent) {
            // More lenient check - only hide if section is truly empty or only contains placeholders
            const textContent = section.textContent.trim().replace(/\s+/g, ' ');
            const onlyUnknownContent = textContent.length < 50 || 
                (textContent.toLowerCase().includes('no information available') && textContent.length < 200) ||
                (textContent.split(' ').filter(word => word !== 'Unknown' && word.length > 2).length < 5);
            
            if (onlyUnknownContent) {
                section.style.display = 'none';
            }
        }
    });
      // Also hide empty subsections within cards (but be more lenient)
    const infoSections = document.querySelectorAll('.info-section');
    infoSections.forEach(section => {
        const ddElements = section.querySelectorAll('dd');
        const listElements = section.querySelectorAll('ul li, ol li');
        const paragraphs = section.querySelectorAll('p');
        
        const hasValidDDContent = Array.from(ddElements).some(dd => 
            dd.textContent.trim() !== '' && 
            dd.textContent.trim() !== 'Unknown'
        );
        
        const hasValidListContent = Array.from(listElements).some(li => 
            li.textContent.trim() !== '' && 
            li.textContent.trim() !== 'Unknown'
        );
        
        const hasValidParagraphs = Array.from(paragraphs).some(p => 
            p.textContent.trim() !== '' && 
            p.textContent.trim() !== 'Unknown' &&
            p.textContent.trim().length > 10
        );
        
        if (!hasValidDDContent && !hasValidListContent && !hasValidParagraphs) {
            section.style.display = 'none';
        }
    });
}

// Format benchmark times with appropriate units
function formatBenchmarkTime(seconds) {
    if (seconds < 1) {
        return `${(seconds * 1000).toFixed(2)} ms`;
    } else if (seconds < 60) {
        return `${seconds.toFixed(2)} s`;
    } else {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}m ${remainingSeconds.toFixed(2)}s`;
    }
}

// Format cost information
function formatCost(cost) {
    if (cost < 0.01) {
        return `${(cost * 100).toFixed(2)}¢`;
    } else {
        return `$${cost.toFixed(2)}`;
    }
}

// Update benchmark display with formatted values
function updateBenchmarkDisplay() {
    // Format timing values
    const timeElements = document.querySelectorAll('[data-benchmark-time]');
    timeElements.forEach(element => {
        const rawTime = parseFloat(element.dataset.benchmarkTime);
        if (!isNaN(rawTime)) {
            element.textContent = formatBenchmarkTime(rawTime);
        }
    });
    
    // Format cost values
    const costElements = document.querySelectorAll('[data-benchmark-cost]');
    costElements.forEach(element => {
        const rawCost = parseFloat(element.dataset.benchmarkCost);
        if (!isNaN(rawCost)) {
            element.textContent = formatCost(rawCost);
        }
    });
    
    // Format token values
    const tokenElements = document.querySelectorAll('[data-benchmark-tokens]');
    tokenElements.forEach(element => {
        const rawTokens = parseInt(element.dataset.benchmarkTokens);
        if (!isNaN(rawTokens)) {
            element.textContent = rawTokens.toLocaleString();
        }
    });
}

// Initialize page functionality
document.addEventListener('DOMContentLoaded', function() {
    // Get institution type from template data
    const institutionTypeElement = document.querySelector('[data-institution-type]');
    if (institutionTypeElement) {
        document.body.dataset.institutionType = institutionTypeElement.dataset.institutionType;
    }
    
    // Apply theme first
    applyInstitutionTheme();
    
    // Update sector-specific icons
    updateSectorIcons();
      // Initialize image counter and pre-validation
    const imageContainers = document.querySelectorAll('[data-image-container], .logo-container, .image-container');
    totalImagesAttempted = imageContainers.length;
    if (totalImagesAttempted > 0) {
        preValidateImages();
    }
    
    // Update benchmark formatting
    updateBenchmarkDisplay();
    
    // Hide empty sections after a brief delay to allow content to load
    setTimeout(() => {
        hideEmptySections();
    }, 200);
    
    // Lazy loading for images
    const images = document.querySelectorAll('img[loading="lazy"]');
    
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });

        images.forEach(img => imageObserver.observe(img));
    }
});
