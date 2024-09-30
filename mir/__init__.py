import os
import pandas as pd
pd.options.mode.copy_on_write = True

if os.getenv("COLAB_RELEASE_TAG"):
    COLAB = True
else:
    COLAB = False
    
if COLAB:
    PROJECT_DIR = os.path.abspath("./MIRProject")
else:
    PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_DIR, 'data')

if not os.path.exists(DATA_DIR):
    os.mkdir(DATA_DIR)