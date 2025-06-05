/**
 * AutocompleteWidget Class
 * 
 * A comprehensive autocomplete widget that supports:
 * - Real-time search suggestions
 * - Spell correction with "Did you mean?" functionality
 * - Preview text showing completion
 * - Keyboard navigation
 * - Mouse interaction
 */
class AutocompleteWidget {
    constructor(inputElement, options = {}) {
        this.input = inputElement;
        this.options = {
            minLength: 2,
            maxSuggestions: 5,
            delay: 300,
            endpoint: '/autocomplete',
            ...options
        };

        this.suggestions = [];
        this.selectedIndex = -1;
        this.isOpen = false;
        this.debounceTimer = null;
        this.isSpellCorrection = false;

        this.init();
    }

    /**
     * Initialize the autocomplete widget
     */
    init() {
        this.createDropdown();
        this.createPreviewText();
        this.attachEventListeners();
    }

    /**
     * Create the dropdown container for suggestions
     */
    createDropdown() {
        // Create dropdown container
        this.dropdown = document.createElement('div');
        this.dropdown.className = 'autocomplete-dropdown';
        this.dropdown.style.display = 'none';

        // Position dropdown relative to input
        this.input.parentNode.style.position = 'relative';
        this.input.parentNode.appendChild(this.dropdown);
    }

    /**
     * Create preview text overlay for autocomplete suggestions
     */
    createPreviewText() {
        // Create a container for the input and preview overlay
        const inputContainer = this.input.parentNode;
        inputContainer.style.position = 'relative';
        inputContainer.classList.add('autocomplete-input-container');

        // Create preview text element
        this.previewText = document.createElement('div');
        this.previewText.className = 'autocomplete-preview';

        // Get computed styles from the input to match exactly
        const inputStyles = window.getComputedStyle(this.input);
        
        // Set styles to match the input exactly
        this.previewText.style.cssText = `
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
            width: ${this.input.offsetWidth}px !important;
            height: ${this.input.offsetHeight}px !important;            
            border: ${inputStyles.border} !important;
            border-color: transparent !important;
            outline: none !important;
            background: transparent !important;
            color: #aaa !important;
            pointer-events: none !important;
            z-index: 1 !important;
            font-size: ${inputStyles.fontSize} !important;
            font-family: ${inputStyles.fontFamily} !important;
            font-weight: ${inputStyles.fontWeight} !important;
            line-height: ${inputStyles.lineHeight} !important;
            padding: ${inputStyles.padding} !important;
            margin: 0 !important;
            box-sizing: ${inputStyles.boxSizing} !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-align: ${inputStyles.textAlign} !important;
            display: none !important;
        `;

        // Insert preview behind the input
        inputContainer.appendChild(this.previewText);

        // Ensure input is above preview
        this.input.style.position = 'relative';
        this.input.style.zIndex = '2';
        this.input.style.background = 'transparent';
    }

    /**
     * Attach all event listeners
     */
    attachEventListeners() {
        // Input events
        this.input.addEventListener('input', (e) => this.handleInput(e));
        this.input.addEventListener('keydown', (e) => this.handleKeydown(e));
        this.input.addEventListener('focus', (e) => this.handleFocus(e));
        this.input.addEventListener('blur', (e) => this.handleBlur(e));

        // Document click to close dropdown
        document.addEventListener('click', (e) => {
            if (!this.input.parentNode.contains(e.target)) {
                this.close();
            }
        });
    }

    /**
     * Handle input changes with debouncing
     */
    handleInput(e) {
        const value = e.target.value.trim();

        // Clear preview text when input changes
        this.clearPreviewText();

        // Clear previous timer
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }

        // Debounce the search
        this.debounceTimer = setTimeout(() => {
            if (value.length >= this.options.minLength) {
                this.search(value);
            } else {
                this.close();
            }
        }, this.options.delay);
    }

    /**
     * Handle keyboard navigation and selection
     */
    handleKeydown(e) {
        if (!this.isOpen) {
            // Handle Tab for autocomplete even when dropdown is closed
            if (e.key === 'Tab' && this.suggestions.length > 0) {
                e.preventDefault();
                this.selectSuggestion(0); // Use first suggestion
                return;
            }
            return;
        }

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                this.selectNext();
                break;
            case 'ArrowUp':
                e.preventDefault();
                this.selectPrevious();
                break;
            case 'Enter':
                e.preventDefault();
                if (this.selectedIndex >= 0) {
                    this.selectSuggestion(this.selectedIndex);
                }
                break;
            case 'Tab':
                e.preventDefault();
                // Use first suggestion if none selected, otherwise use selected
                const indexToUse = this.selectedIndex >= 0 ? this.selectedIndex : 0;
                this.selectSuggestion(indexToUse);
                break;
            case 'Escape':
                this.close();
                break;
        }
    }

    /**
     * Handle input focus
     */
    handleFocus(e) {
        const value = e.target.value.trim();
        if (value.length >= this.options.minLength && this.suggestions.length > 0) {
            this.open();
        }
    }

    /**
     * Handle input blur with delay for suggestion clicks
     */
    handleBlur(e) {
        // Delay closing to allow clicking on suggestions
        setTimeout(() => {
            this.close();
        }, 150);
    }

    /**
     * Perform search and handle response
     */
    async search(query) {
        try {
            const response = await fetch(`${this.options.endpoint}?term=${encodeURIComponent(query)}`);
            const data = await response.json();

            // Handle the new response format that includes spell correction
            let suggestions = [];
            let isSpellCorrection = false;
            if (Array.isArray(data)) {
                // Old format or direct suggestions array
                suggestions = data;
            } else if (data && typeof data === 'object') {
                // New format with metadata
                suggestions = data.suggestions || [];
                isSpellCorrection = data.source === 'spell_correction';

                console.log('DEBUG: Response data:', data);
                console.log('DEBUG: isSpellCorrection:', isSpellCorrection);
                console.log('DEBUG: First suggestion:', suggestions[0]);
            }

            this.suggestions = suggestions;
            this.selectedIndex = -1;
            this.isSpellCorrection = isSpellCorrection;

            // Update preview text with first suggestion
            this.updatePreviewText();

            if (suggestions.length > 0) {
                this.render();
                this.open();
            } else {
                this.close();
            }
        } catch (error) {
            console.error('Autocomplete search failed:', error);
            this.close();
        }
    }

    /**
     * Update preview text showing completion
     */
    updatePreviewText() {
        if (!this.previewText) return;

        const currentValue = this.input.value;
        this.clearPreviewText();

        // Only show preview for regular autocomplete, not spell corrections
        if (this.suggestions.length > 0 && currentValue.length > 0 && !this.isSpellCorrection) {
            const firstSuggestion = this.suggestions[0];
            let suggestionText = '';

            if (typeof firstSuggestion === 'object') {
                suggestionText = firstSuggestion.full_name || firstSuggestion.name || firstSuggestion.term || '';
            } else {
                suggestionText = firstSuggestion;
            }

            // Check if the suggestion starts with the current input (case insensitive)
            if (suggestionText.toLowerCase().startsWith(currentValue.toLowerCase())) {
                const completionPart = suggestionText.substring(currentValue.length);

                if (completionPart.length > 0) {
                    // Create preview text with invisible user input + grey completion
                    this.previewText.innerHTML = `<span style="color: transparent; user-select: none;">${currentValue}</span><span style="color: #aaa;">${completionPart}</span>`;
                    this.previewText.style.display = 'block';
                    
                    console.log('DEBUG: Preview text set:', this.previewText.innerHTML);
                    console.log('DEBUG: Preview display:', this.previewText.style.display);
                }
            }
        }
    }

    /**
     * Clear the preview text
     */
    clearPreviewText() {
        if (this.previewText) {
            this.previewText.style.display = 'none';
            this.previewText.innerHTML = '';
            console.log('DEBUG: Preview text cleared');
        }
    }

    /**
     * Show spell correction message
     */
    showSpellCorrectionMessage(message, originalQuery) {
        // Create or update a message element to show "Did you mean" suggestions
        let messageElement = this.input.parentNode.querySelector('.spell-correction-message');
        if (!messageElement) {
            messageElement = document.createElement('div');
            messageElement.className = 'spell-correction-message';
            this.input.parentNode.appendChild(messageElement);
        }

        messageElement.innerHTML = `
            <div class="spell-correction-content">
                <span class="spell-correction-text">${message}</span>
                <small class="original-query">You searched for: "${originalQuery}"</small>
            </div>
        `;

        // Auto-hide the message after 5 seconds
        setTimeout(() => {
            if (messageElement) {
                messageElement.remove();
            }
        }, 5000);
    }

    /**
     * Render suggestions in the dropdown
     */
    render() {
        this.dropdown.innerHTML = '';

        // Add a separate "Did you mean?" section for spell corrections
        if (this.isSpellCorrection && this.suggestions.length > 0) {
            console.log('DEBUG: Creating "Did you mean?" section');
            const firstSuggestion = this.suggestions[0];
            console.log('DEBUG: First suggestion for did you mean:', firstSuggestion);

            if (firstSuggestion && firstSuggestion.corrected_query) {
                console.log('DEBUG: Adding "Did you mean?" section with corrected_query:', firstSuggestion.corrected_query);
                
                // Create "Did you mean?" section
                const didYouMeanSection = document.createElement('div');
                didYouMeanSection.className = 'did-you-mean-section';
                const didYouMeanText = document.createElement('div');
                didYouMeanText.className = 'did-you-mean-text';
                didYouMeanText.style.cursor = 'pointer';

                // Add click handler to apply the correction
                didYouMeanText.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this.applyCorrectedQuery(firstSuggestion.corrected_query);
                });

                if (firstSuggestion.corrections && firstSuggestion.corrections.length > 0) {
                    // Show highlighted corrections
                    const correctedText = this.highlightCorrections(
                        firstSuggestion.original_query,
                        firstSuggestion.corrections
                    );
                    didYouMeanText.innerHTML = `<span class="correction-icon">📝</span> Did you mean: ${correctedText}?`;
                } else {
                    // Simple fallback
                    didYouMeanText.innerHTML = `<span class="correction-icon">📝</span> Did you mean: <em>${firstSuggestion.corrected_query}</em>?`;
                }

                didYouMeanSection.appendChild(didYouMeanText);
                this.dropdown.appendChild(didYouMeanSection);

                // Add a separator
                const separator = document.createElement('div');
                separator.className = 'spell-correction-separator';
                separator.innerHTML = '<hr style="margin: 0; border-color: #ffeaa7;">';
                this.dropdown.appendChild(separator);
            }
        }

        this.suggestions.forEach((suggestion, index) => {
            const item = document.createElement('div');
            item.className = 'autocomplete-item';
            if (this.isSpellCorrection) {
                item.classList.add('spell-correction-item');
            }
            item.dataset.index = index;

            // Handle both old string format and new object format for backward compatibility
            let institutionName, institutionType, fullName, isSpellCorrection;
            if (typeof suggestion === 'object' && (suggestion.name || suggestion.full_name || suggestion.term)) {
                institutionName = suggestion.name || suggestion.full_name || suggestion.term;
                institutionType = suggestion.type || suggestion.institution_type || '';
                fullName = suggestion.full_name || suggestion.name || suggestion.term;
                isSpellCorrection = suggestion.is_spell_correction || suggestion.spell_correction || suggestion.suggestion_type === 'spell_correction';
            } else {
                // Fallback for old string format
                institutionName = suggestion;
                institutionType = '';
                fullName = suggestion;
                isSpellCorrection = this.isSpellCorrection;
            }

            // Create the display structure with proper alignment
            if (institutionType) {
                item.innerHTML = `
                    <div class="autocomplete-item-content">
                        <span class="institution-name">${institutionName}</span>
                        <span class="institution-type">(${institutionType})</span>
                    </div>
                `;
            } else {
                item.innerHTML = `
                    <div class="autocomplete-item-content">
                        <span class="institution-name">${institutionName}</span>
                    </div>
                `;
            }

            // Store the full name for selection
            item.dataset.fullName = fullName;

            // Highlight matching text in the institution name
            const query = this.input.value.trim();
            if (query && !isSpellCorrection) {
                // Only highlight for regular autocomplete, not spell corrections
                const nameSpan = item.querySelector('.institution-name');
                const regex = new RegExp(`(${this.escapeRegex(query)})`, 'gi');
                nameSpan.innerHTML = nameSpan.textContent.replace(regex, '<strong>$1</strong>');
            }

            // Click handler
            item.addEventListener('mousedown', (e) => {
                e.preventDefault();
                this.selectSuggestion(index);
            });

            // Hover handler
            item.addEventListener('mouseenter', () => {
                this.setSelected(index);
            });

            this.dropdown.appendChild(item);
        });

        // Update preview text based on current input
        this.updatePreviewText();
    }

    /**
     * Navigation methods
     */
    selectNext() {
        this.selectedIndex = Math.min(this.selectedIndex + 1, this.suggestions.length - 1);
        this.updateSelection();
    }

    selectPrevious() {
        this.selectedIndex = Math.max(this.selectedIndex - 1, -1);
        this.updateSelection();
    }

    setSelected(index) {
        this.selectedIndex = index;
        this.updateSelection();
    }

    updateSelection() {
        const items = this.dropdown.querySelectorAll('.autocomplete-item');
        items.forEach((item, index) => {
            item.classList.toggle('selected', index === this.selectedIndex);
        });
    }

    /**
     * Select a suggestion and close dropdown
     */
    selectSuggestion(index) {
        if (index >= 0 && index < this.suggestions.length) {
            // Handle both old string format and new object format
            const suggestion = this.suggestions[index];
            let valueToSet;

            if (typeof suggestion === 'object' && suggestion.full_name) {
                valueToSet = suggestion.full_name;
            } else if (typeof suggestion === 'object' && suggestion.name) {
                valueToSet = suggestion.name;
            } else {
                valueToSet = suggestion;
            }

            this.input.value = valueToSet;
            this.close();
            this.input.focus();

            // Trigger input event for any listeners
            this.input.dispatchEvent(new Event('input', { bubbles: true }));
        }
    }

    /**
     * Open the dropdown
     */
    open() {
        this.isOpen = true;
        this.dropdown.style.display = 'block';
    }

    /**
     * Close the dropdown
     */
    close() {
        this.isOpen = false;
        this.dropdown.style.display = 'none';
        this.selectedIndex = -1;

        // Clear preview text when closing
        this.clearPreviewText();
    }

    /**
     * Utility method to escape regex characters
     */
    escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    /**
     * Highlight corrections in spell correction suggestions
     */
    highlightCorrections(originalQuery, corrections) {
        /**
         * Create a visual representation showing what was corrected
         * @param {string} originalQuery - The original search query
         * @param {Array} corrections - Array of correction objects
         * @returns {string} HTML string with corrections highlighted
         */
        if (!corrections || corrections.length === 0) {
            return `<em>${originalQuery}</em>`;
        }

        const words = originalQuery.toLowerCase().split(' ');
        const correctedWords = [...words]; // Copy original words

        // Apply corrections
        corrections.forEach(correction => {
            if (correction.position < correctedWords.length) {
                correctedWords[correction.position] = correction.corrected;
            }
        });

        // Create HTML with corrections highlighted
        const htmlWords = words.map((word, index) => {
            const correction = corrections.find(c => c.position === index);
            if (correction) {
                return `<span class="spell-correction-word" title="Changed from '${correction.original}'">${correction.corrected}</span>`;
            }
            return word;
        });

        return `<em>${htmlWords.join(' ')}</em>`;
    }

    /**
     * Apply corrected query from spell correction
     */
    applyCorrectedQuery(correctedQuery) {
        // Apply the corrected query to the input
        this.input.value = correctedQuery;

        // Clear preview text
        this.clearPreviewText();

        // Trigger a new search with the corrected query
        this.search(correctedQuery);

        // Focus back on the input
        this.input.focus();

        // Move cursor to end
        this.input.setSelectionRange(correctedQuery.length, correctedQuery.length);
    }
}
