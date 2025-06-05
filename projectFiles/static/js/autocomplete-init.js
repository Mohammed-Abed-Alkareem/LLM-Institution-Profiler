/**
 * Autocomplete Initialization and Utility Functions
 * 
 * This file handles the initialization of autocomplete widgets
 * and provides utility functions for autocomplete functionality.
 */

/**
 * Default configuration for autocomplete widgets
 */
const AUTOCOMPLETE_DEFAULTS = {
    minLength: 2,
    maxSuggestions: 5,
    delay: 300,
    endpoint: '/autocomplete'
};

/**
 * Autocomplete initialization class
 */
class AutocompleteInitializer {
    constructor() {
        this.widgets = new Map();
    }

    /**
     * Initialize autocomplete for a specific input element
     * @param {HTMLElement} inputElement - The input element to enhance
     * @param {Object} options - Configuration options
     * @returns {AutocompleteWidget} The created widget instance
     */
    initializeWidget(inputElement, options = {}) {
        if (!inputElement) {
            console.error('AutocompleteInitializer: Input element is required');
            return null;
        }

        const mergedOptions = { ...AUTOCOMPLETE_DEFAULTS, ...options };
        const widget = new AutocompleteWidget(inputElement, mergedOptions);
        
        // Store widget reference for potential cleanup
        this.widgets.set(inputElement, widget);
        
        return widget;
    }

    /**
     * Initialize autocomplete for all elements matching a selector
     * @param {string} selector - CSS selector for input elements
     * @param {Object} options - Configuration options
     * @returns {Array} Array of created widget instances
     */
    initializeAll(selector, options = {}) {
        const elements = document.querySelectorAll(selector);
        const widgets = [];

        elements.forEach(element => {
            const widget = this.initializeWidget(element, options);
            if (widget) {
                widgets.push(widget);
            }
        });

        return widgets;
    }

    /**
     * Get widget instance for a specific input element
     * @param {HTMLElement} inputElement - The input element
     * @returns {AutocompleteWidget|null} The widget instance or null
     */
    getWidget(inputElement) {
        return this.widgets.get(inputElement) || null;
    }

    /**
     * Destroy widget for a specific input element
     * @param {HTMLElement} inputElement - The input element
     */
    destroyWidget(inputElement) {
        const widget = this.widgets.get(inputElement);
        if (widget) {
            // Clean up event listeners and DOM elements
            widget.close();
            if (widget.dropdown && widget.dropdown.parentNode) {
                widget.dropdown.parentNode.removeChild(widget.dropdown);
            }
            if (widget.previewText && widget.previewText.parentNode) {
                widget.previewText.parentNode.removeChild(widget.previewText);
            }
            this.widgets.delete(inputElement);
        }
    }

    /**
     * Destroy all widget instances
     */
    destroyAll() {
        this.widgets.forEach((widget, element) => {
            this.destroyWidget(element);
        });
    }
}

/**
 * Utility functions for autocomplete
 */
class AutocompleteUtils {
    /**
     * Validate autocomplete configuration
     * @param {Object} options - Configuration options to validate
     * @returns {Object} Validated and sanitized options
     */
    static validateOptions(options = {}) {
        const validated = { ...options };

        // Ensure minimum length is reasonable
        if (typeof validated.minLength !== 'number' || validated.minLength < 1) {
            validated.minLength = AUTOCOMPLETE_DEFAULTS.minLength;
        }

        // Ensure max suggestions is reasonable
        if (typeof validated.maxSuggestions !== 'number' || validated.maxSuggestions < 1) {
            validated.maxSuggestions = AUTOCOMPLETE_DEFAULTS.maxSuggestions;
        }

        // Ensure delay is reasonable
        if (typeof validated.delay !== 'number' || validated.delay < 0) {
            validated.delay = AUTOCOMPLETE_DEFAULTS.delay;
        }

        // Ensure endpoint is a string
        if (typeof validated.endpoint !== 'string') {
            validated.endpoint = AUTOCOMPLETE_DEFAULTS.endpoint;
        }

        return validated;
    }

    /**
     * Check if an element is suitable for autocomplete
     * @param {HTMLElement} element - Element to check
     * @returns {boolean} True if suitable, false otherwise
     */
    static isValidInputElement(element) {
        if (!element || !element.tagName) {
            return false;
        }

        const tagName = element.tagName.toLowerCase();
        const type = element.type ? element.type.toLowerCase() : '';

        // Check if it's an input element of appropriate type
        if (tagName === 'input') {
            return ['text', 'search', 'email', 'url', ''].includes(type);
        }

        // Check if it's a textarea
        if (tagName === 'textarea') {
            return true;
        }

        // Check if it's a contenteditable element
        if (element.contentEditable === 'true') {
            return true;
        }

        return false;
    }

    /**
     * Get input element position for dropdown positioning
     * @param {HTMLElement} inputElement - The input element
     * @returns {Object} Position information
     */
    static getInputPosition(inputElement) {
        const rect = inputElement.getBoundingClientRect();
        const computedStyle = window.getComputedStyle(inputElement);
        
        return {
            top: rect.top + window.scrollY,
            left: rect.left + window.scrollX,
            width: rect.width,
            height: rect.height,
            borderWidth: {
                top: parseInt(computedStyle.borderTopWidth, 10) || 0,
                right: parseInt(computedStyle.borderRightWidth, 10) || 0,
                bottom: parseInt(computedStyle.borderBottomWidth, 10) || 0,
                left: parseInt(computedStyle.borderLeftWidth, 10) || 0
            },
            padding: {
                top: parseInt(computedStyle.paddingTop, 10) || 0,
                right: parseInt(computedStyle.paddingRight, 10) || 0,
                bottom: parseInt(computedStyle.paddingBottom, 10) || 0,
                left: parseInt(computedStyle.paddingLeft, 10) || 0
            }
        };
    }

    /**
     * Debounce function for search requests
     * @param {Function} func - Function to debounce
     * @param {number} delay - Delay in milliseconds
     * @returns {Function} Debounced function
     */
    static debounce(func, delay) {
        let timeoutId;
        return function (...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => func.apply(this, args), delay);
        };
    }

    /**
     * Escape HTML special characters
     * @param {string} text - Text to escape
     * @returns {string} Escaped text
     */
    static escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Highlight matching text in a string
     * @param {string} text - Text to highlight in
     * @param {string} query - Query to highlight
     * @returns {string} HTML with highlighted matches
     */
    static highlightMatch(text, query) {
        if (!query || !text) {
            return AutocompleteUtils.escapeHtml(text);
        }

        const escapedQuery = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const regex = new RegExp(`(${escapedQuery})`, 'gi');
        const escapedText = AutocompleteUtils.escapeHtml(text);
        
        return escapedText.replace(regex, '<strong>$1</strong>');
    }
}

// Global instance for easy access
const autocompleteInitializer = new AutocompleteInitializer();

/**
 * Initialize autocomplete when DOM is loaded
 */
document.addEventListener('DOMContentLoaded', function () {
    // Initialize autocomplete for institution name input
    const institutionInput = document.querySelector('input[name="institution_name"]');
    if (institutionInput) {
        autocompleteInitializer.initializeWidget(institutionInput, {
            minLength: 2,
            maxSuggestions: 5,
            delay: 300
        });
    }

    // You can add more initializations here for other inputs
    // Example:
    // const otherInputs = document.querySelectorAll('.autocomplete-enabled');
    // autocompleteInitializer.initializeAll('.autocomplete-enabled', customOptions);
});

/**
 * Clean up on page unload
 */
window.addEventListener('beforeunload', function () {
    autocompleteInitializer.destroyAll();
});

// Export for module usage (if using modules)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        AutocompleteInitializer,
        AutocompleteUtils,
        AUTOCOMPLETE_DEFAULTS
    };
}
