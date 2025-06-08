# go here to download it https://spacy.io/usage 

# for me on linux it was
# pip install -U pip setuptools wheel
#pip install -U spacy
#python -m spacy download en_core_web_sm

import spacy

nlp = spacy.load("en_core_web_sm")

def is_organization(name):
    doc = nlp(name)
    for ent in doc.ents:
        if ent.text.lower() == name.lower() and ent.label_ == "ORG":
            return True
    return False

def capitalize_name(name):
    """
    Capitalizes the first letter of each word in the name, including after hyphens.
    """
    def cap_word(word):
        return '-'.join(part.capitalize() for part in word.split('-'))
    return ' '.join(cap_word(word) for word in name.split())


# Example usage
input_name = "Tel-Aviv University"
input_name = capitalize_name(input_name)
if is_organization(input_name):
    print(f"✅ '{input_name}' is an organization.")
else:
    print(f"❌ '{input_name}' is not recognized as an organization.")
