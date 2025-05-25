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