from collections import defaultdict
from mir import DATA_DIR, COLAB
import pandas as pd
import os
import json
import unidecode

def get_dataset(verbose=False) -> pd.DataFrame:
    """
    Downloads or loads the dataset from the data directory.
    Languages other than English are filtered out.
    """
    filtered_df_path = f"{DATA_DIR}/filtered-lyrics-data.csv"
    
    if not os.path.exists(filtered_df_path):
        if not os.path.exists(f"{DATA_DIR}/lyrics-data.csv"):
            if verbose:
                print("Downloading dataset...")
            kaggle_handle = "neisse/scrapped-lyrics-from-6-genres"
            if COLAB:
                from google.colab import userdata # type: ignore
                kaggle_data = json.loads(userdata.get("kaggle"))
            else:
                if not os.path.exists(f"{DATA_DIR}/kaggle.json"):
                    raise FileNotFoundError("Kaggle API credentials not found. Please add kaggle.json to the data directory.")
                with open(f"{DATA_DIR}/kaggle.json") as f:
                    kaggle_data = json.load(f)
            os.environ["KAGGLE_USERNAME"] = kaggle_data["username"]
            os.environ["KAGGLE_KEY"] = kaggle_data["key"]
            import kaggle
            kaggle.api.dataset_download_files(
                kaggle_handle, 
                path=DATA_DIR, 
                unzip=True, 
                quiet=not verbose
            )
        if verbose:
            print("Filtering dataset...")
        df = pd.read_csv(f"{DATA_DIR}/lyrics-data.csv")
        df.dropna(inplace=True)
        filtered_df = df[df.loc[:, 'language'] == 'en']
        filtered_df.rename(columns={"ALink": "artist", "SName": "song", "Lyric": "lyrics"}, inplace=True)
        filtered_df.drop(columns=["language", "SLink"], inplace=True)
        
        def fix_name(name: str):
            return " ".join([
                name_part
                    .capitalize() 
                for name_part in 
                name[1:-1]
                    .replace("-"," ")
                    .split()
            ])
            
        def fix_song(song: str):
            return unidecode.unidecode(song)
        
        def fix_lyrics(lyrics: str):
            return unidecode.unidecode(lyrics.replace("\n", " "))
            
        filtered_df.loc[:, 'artist'] = filtered_df['artist'].map(fix_name)
        filtered_df.loc[:, 'song'] = filtered_df['song'].map(fix_song)
        filtered_df.loc[:, 'lyrics'] = filtered_df['lyrics'].map(fix_lyrics)
        filtered_df.reset_index(drop=True, inplace=True)
        filtered_df.to_csv(filtered_df_path, index=False)
        os.remove(f"{DATA_DIR}/lyrics-data.csv")
        os.remove(f"{DATA_DIR}/artists-data.csv")
    else:
        if verbose:
            print("Loading dataset...")
        filtered_df = pd.read_csv(filtered_df_path)
    if verbose:
        print("Dataset loaded.")
    return filtered_df
    
if __name__ == "__main__":
    df = get_dataset(verbose=True)
    print(df)
    