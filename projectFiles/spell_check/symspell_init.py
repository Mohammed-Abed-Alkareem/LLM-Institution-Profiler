import pandas as pd
from symspellpy import SymSpell, Verbosity

def create_symspell_dict(csv_files : list , dictionary_path : str):
    """
    Create a SymSpell dictionary from a list of CSV files.
    
    Args:
        csv_files (list): List of paths to CSV files containing words.
        dictionary_path (str): Path to save the SymSpell dictionary.
    """
    for csv_file in csv_files:
        if not csv_file.endswith('.csv'):
            raise ValueError(f"File {csv_file} is not a CSV file.")
        
        #if file name list_of_univs.csv 
        if 'list_of_univs' in csv_file:
            #get column 6 
            df = pd.read_csv(csv_file, usecols=[5])
            print(df.head())
            with open(dictionary_path, 'w', encoding='utf-8') as f:
                for word in df['name']:
                    f.write(f"{word.lower()},1\n")

if __name__ == "__main__":
    # Example usage
    csv_files = ['./list_of_univs.csv']
    dictionary_path = './symspell_dict.txt'
    
    create_symspell_dict(csv_files, dictionary_path)
    
    print("SymSpell dictionary created")
