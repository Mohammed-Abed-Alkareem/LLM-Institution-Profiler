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
        
        this.init();
    }
    
    init() {
        this.createDropdown();
        this.attachEventListeners();
    }
    
    createDropdown() {
        // Create dropdown container
        this.dropdown = document.createElement('div');
        this.dropdown.className = 'autocomplete-dropdown';
        this.dropdown.style.display = 'none';
        
        // Position dropdown relative to input
        this.input.parentNode.style.position = 'relative';
        this.input.parentNode.appendChild(this.dropdown);
    }
    
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
    
    handleInput(e) {
        const value = e.target.value.trim();
        
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
    
    handleKeydown(e) {
        if (!this.isOpen) return;
        
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
            case 'Escape':
                this.close();
                break;
        }
    }
    
    handleFocus(e) {
        const value = e.target.value.trim();
        if (value.length >= this.options.minLength && this.suggestions.length > 0) {
            this.open();
        }
    }
    
    handleBlur(e) {
        // Delay closing to allow clicking on suggestions
        setTimeout(() => {
            this.close();
        }, 150);
    }
    
    async search(query) {
        try {
            const response = await fetch(`${this.options.endpoint}?term=${encodeURIComponent(query)}`);
            const suggestions = await response.json();
            
            this.suggestions = suggestions;
            this.selectedIndex = -1;
            
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
    
    render() {
        this.dropdown.innerHTML = '';
        
        this.suggestions.forEach((suggestion, index) => {
            const item = document.createElement('div');
            item.className = 'autocomplete-item';
            item.textContent = suggestion;
            item.dataset.index = index;
            
            // Highlight matching text
            const query = this.input.value.trim();
            if (query) {
                const regex = new RegExp(`(${this.escapeRegex(query)})`, 'gi');
                item.innerHTML = suggestion.replace(regex, '<strong>$1</strong>');
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
    }
    
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
    
    selectSuggestion(index) {
        if (index >= 0 && index < this.suggestions.length) {
            this.input.value = this.suggestions[index];
            this.close();
            this.input.focus();
            
            // Trigger input event for any listeners
            this.input.dispatchEvent(new Event('input', { bubbles: true }));
        }
    }
    
    open() {
        this.isOpen = true;
        this.dropdown.style.display = 'block';
    }
    
    close() {
        this.isOpen = false;
        this.dropdown.style.display = 'none';
        this.selectedIndex = -1;
    }
    
    escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }
}

// Initialize autocomplete when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const institutionInput = document.querySelector('input[name="institution_name"]');
    if (institutionInput) {
        new AutocompleteWidget(institutionInput, {
            minLength: 2,
            maxSuggestions: 5,
            delay: 300
        });
    }
});
