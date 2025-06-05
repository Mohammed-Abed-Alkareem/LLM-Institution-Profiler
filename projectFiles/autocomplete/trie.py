class TrieNode:
    """A node in the Trie data structure."""
    
    def __init__(self):
        self.children = {}
        self.is_end_word = False
        self.word = None  # Store the complete word at end nodes
        self.frequency = 0  # For ranking suggestions
        self.institution_type = None  # Store institution type (Edu, Fin, Med)


class Trie:
    """
    Trie (Prefix Tree) implementation for efficient autocomplete functionality.
    Supports case-insensitive search and frequency-based ranking.
    """
    
    def __init__(self):
        self.root = TrieNode()
        self.word_count = 0
    
    def insert(self, word, frequency=1, institution_type=None):
        """
        Insert a word into the trie with optional frequency for ranking and institution type.
        
        Args:
            word (str): The word to insert
            frequency (int): Frequency/weight of the word for ranking
            institution_type (str): Type of institution (Edu, Fin, Med)
        """
        if not word:
            return
            
        node = self.root
        word_lower = word.lower()
        
        for char in word_lower:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        
        if not node.is_end_word:
            self.word_count += 1
            
        node.is_end_word = True
        node.word = word  # Store original case
        node.frequency = max(node.frequency, frequency)
        node.institution_type = institution_type
    
    def search(self, word):
        """
        Check if a word exists in the trie.
        
        Args:
            word (str): The word to search for
            
        Returns:
            bool: True if word exists, False otherwise
        """
        node = self._find_node(word.lower())
        return node is not None and node.is_end_word
    
    def starts_with(self, prefix):
        """
        Check if any word in the trie starts with the given prefix.
        
        Args:
            prefix (str): The prefix to check
            
        Returns:
            bool: True if prefix exists, False otherwise
        """
        return self._find_node(prefix.lower()) is not None
    def get_suggestions(self, prefix, max_suggestions=5):
        """
        Get autocomplete suggestions for a given prefix.
        
        Args:
            prefix (str): The prefix to get suggestions for
            max_suggestions (int): Maximum number of suggestions to return
            
        Returns:
            list: List of suggestion dictionaries with 'name' and 'type' keys
        """
        if not prefix:
            return []
            
        prefix_lower = prefix.lower()
        prefix_node = self._find_node(prefix_lower)
        
        if prefix_node is None:
            return []
        
        suggestions = []
        self._collect_words(prefix_node, suggestions)
        
        # Sort by frequency (descending) and then alphabetically
        suggestions.sort(key=lambda x: (-x[1], x[0]))
        
        # Return structured data instead of formatted strings
        formatted_suggestions = []
        max_name_length = 50  # Maximum length for institution names
        
        for word, _, institution_type in suggestions[:max_suggestions]:
            # Truncate long names
            if len(word) > max_name_length:
                truncated_word = word[:max_name_length - 3] + "..."
            else:
                truncated_word = word
                
            suggestion = {
                'name': truncated_word,
                'type': institution_type or '',
                'full_name': word  # Keep original for input value
            }
            formatted_suggestions.append(suggestion)
        
        return formatted_suggestions
    
    def _find_node(self, prefix):
        """
        Find the node corresponding to a prefix.
        
        Args:
            prefix (str): The prefix to find
            
        Returns:
            TrieNode or None: The node if found, None otherwise
        """
        node = self.root
        for char in prefix:
            if char not in node.children:
                return None
            node = node.children[char]
        return node
    
    def _collect_words(self, node, words_list):
        """
        Recursively collect all words from a given node.
        
        Args:
            node (TrieNode): The starting node
            words_list (list): List to append found words to
        """
        if node.is_end_word:
            words_list.append((node.word, node.frequency, node.institution_type))
        
        for child in node.children.values():
            self._collect_words(child, words_list)
    
    def get_all_words(self):
        """
        Get all words stored in the trie.
        
        Returns:
            list: List of all words sorted by frequency
        """
        words = []
        self._collect_words(self.root, words)
        words.sort(key=lambda x: (-x[1], x[0]))
        return [word for word, _, _ in words]
    
    def size(self):
        """
        Get the number of words in the trie.
        
        Returns:
            int: Number of words
        """
        return self.word_count
