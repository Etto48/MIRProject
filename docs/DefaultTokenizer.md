<!-- module: mir.ir.impls.default_tokenizers -->

## Default Tokenizer

The `DefaultTokenizer` class tokenizes and preprocesses text for information retrieval tasks.

It uses NLTK's SnowballStemmer, removes punctuation, separates numbers, and eliminates stopwords.

It provides methods to tokenize both queries and documents by processing the text into a list of tokens, each associated with its respective location (e.g., author, title, body, or query).

The `preprocess()` method handles the following tasks:
- **Text normalization**: Converts Unicode characters to ASCII.
- **Punctuation removal**: Removes all punctuation marks.
- **Number separation**: Separates numbers with spaces.
- **Stopword elimination**: Removes common words that don’t carry significant meaning.
- **Stemming**: Reduces words to their root form using NLTK's SnowballStemmer.