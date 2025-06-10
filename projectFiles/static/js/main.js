function showLoadingIndicator() {
  const resultsArea = document.getElementById('results-area');
  if (resultsArea) {
    resultsArea.style.display = 'none';
    /* Hide previous results */
  }
  const loadingIndicator = document.getElementById('loading-indicator');
  if (loadingIndicator) {
    loadingIndicator.style.display = 'block';
  }
}

// Hide loading if results are present on page load
// (after form submission and page reload)
window.addEventListener('load', function () {
  const resultsArea = document.getElementById('results-area');
  const loadingIndicator = document.getElementById('loading-indicator');

  if (resultsArea && loadingIndicator) {
    loadingIndicator.style.display = 'none';
    resultsArea.style.display = 'block';
  } else if (loadingIndicator) {
    loadingIndicator.style.display = 'none';
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
        toggleIcon.className = 'fas fa-sliders-h me-2 text-primary';
        toggleText.textContent = 'Hide Options';
        toggleButton.classList.remove('btn-light');
        toggleButton.classList.add('btn-outline-primary');
      } else {
        // Hide panel
        additionalPanel.classList.remove('show');
        toggleIcon.className = 'fas fa-sliders-h me-2';
        toggleText.textContent = 'Refine Search';
        toggleButton.classList.remove('btn-outline-primary');
        toggleButton.classList.add('btn-light');
      }
    });
  }
});