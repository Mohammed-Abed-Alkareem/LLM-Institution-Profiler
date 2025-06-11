function showLoadingIndicator() {
  const resultsArea = document.getElementById('results-area');
  if (resultsArea) {
    resultsArea.style.display = 'none';
  }
  
  const loadingOverlay = document.getElementById('loading-overlay');
  if (loadingOverlay) {
    loadingOverlay.style.display = 'flex';
    
    // Start the step animation
    startLoadingSteps();
  }
}

function startLoadingSteps() {
  const steps = ['search', 'crawl', 'extract'];
  let currentStep = 0;
  
  // Activate first step immediately
  activateStep(steps[currentStep]);
  
  const stepInterval = setInterval(() => {
    if (currentStep < steps.length - 1) {
      completeStep(steps[currentStep]);
      currentStep++;
      activateStep(steps[currentStep]);
    } else {
      // Keep the last step active until page loads
      clearInterval(stepInterval);
    }
  }, 8000); // 8 seconds between steps
  
  // Store interval for cleanup
  window.loadingStepInterval = stepInterval;
}

function activateStep(stepName) {
  const step = document.querySelector(`[data-step="${stepName}"]`);
  if (step) {
    step.classList.add('active');
  }
}

function completeStep(stepName) {
  const step = document.querySelector(`[data-step="${stepName}"]`);
  if (step) {
    step.classList.remove('active');
    step.classList.add('completed');
  }
}

// Hide loading if results are present on page load
window.addEventListener('load', function () {
  const resultsArea = document.getElementById('results-area');
  const loadingOverlay = document.getElementById('loading-overlay');

  // Clean up any running step animation
  if (window.loadingStepInterval) {
    clearInterval(window.loadingStepInterval);
  }

  if (resultsArea && loadingOverlay) {
    loadingOverlay.style.display = 'none';
    resultsArea.style.display = 'block';
  } else if (loadingOverlay) {
    loadingOverlay.style.display = 'none';
  }
});

// Additional Info Toggle Functionality
document.addEventListener('DOMContentLoaded', function() {
  const toggleButton = document.getElementById('toggle-additional-info');
  const additionalPanel = document.getElementById('additional-info-panel');
  const toggleIcon = document.getElementById('toggle-icon');
  const toggleText = document.getElementById('toggle-text');
  
  if (toggleButton && additionalPanel && toggleIcon && toggleText) {
    toggleButton.addEventListener('click', function() {
      const isCollapsed = !additionalPanel.classList.contains('show');
      
      if (isCollapsed) {
        // Show panel
        additionalPanel.classList.add('show');
        toggleIcon.className = 'fas fa-sliders-h me-2';
        toggleText.textContent = 'Hide Advanced Options';
        toggleButton.classList.remove('btn-outline-secondary');
        toggleButton.classList.add('btn-outline-primary');
      } else {
        // Hide panel
        additionalPanel.classList.remove('show');
        toggleIcon.className = 'fas fa-sliders-h me-2';
        toggleText.textContent = 'Advanced Search Options';
        toggleButton.classList.remove('btn-outline-primary');
        toggleButton.classList.add('btn-outline-secondary');
      }
    });
  }
});