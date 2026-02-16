# RAG_Movie_Searcher
This project is a movie search engine that uses Retrieval-Augmented Generation (RAG) to provide users with relevant information about movies based on their queries. 

# How it works
1. The application uses Whoosh to create an index of movie-related documents (e.g., subtitles, descriptions).
2. When a user submits a query, the search engine retrieves relevant documents from the index based on the query.
3. The retrieved documents are then used to generate a response using a language model (e.g., GPT-3.5-turbo) to provide users with information about the movies they are interested in.
4. The search results and suggestions are displayed to users in an interactive interface built with Streamlit.

Here is a snapshot of the application:
![alt text](<Screenshot (1090).png>)


## Installation 
1. Clone the repository:
   ```bash
   git clone
    ```
2. Navigate to the project directory:
   ```bash
   cd RAG_Movie_Searcher
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
1. put your .srt files in the `src/documents` directory.
2. Create the Whoosh index by running the indexing script:
   ```bash
   python scripts/create_index.py
   ```
3. export Python path to src:
   ```bash
   export PYTHONPATH=./src
   ```
4. Set environment variable for OpenAI API key:
   ```bash
   export My_API_KEY="your_openai_api_key"
   ```
5. Run the main application:
   ```bash
   streamlit run src/app/main.py
   ```
6. Open the provided URL in your web browser to access the movie search engine. 
7. Enter your movie-related queries in the search bar and view the results and suggestions.

The structure of the project is as follows:
```RAG_Movie_Searcher/
├── src/
│   ├── __init__.py
│   ├── app/
│   │   ├── constants.py
│   │   ├── llm.py
│   │   ├── main.py
│   │   ├── search.py
│   │   └── srt_tools.py
│   ├── documents/
│   └── index/
├── scripts/
│   └── create_index.py
├── .gitignore
├── README.md
└── requirements.txt
```