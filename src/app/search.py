from whoosh import index
from whoosh.qparser import QueryParser
from whoosh.query import Or, Term

from src import DATA_DIR, INDEX_DIR
from src.app.constants import SCHEMA
from typing import List, Dict

class SearchEngine:
    """A search engine for querying SRT subtitle files.
    Uses Whoosh to index and search subtitle content.
        - On initialization, it loads the index from disk (or rebuilds it if specified).
        - When called with a query string, it searches the index and returns matching documents with highlights.
    """
    def __init__(self, index_dir: str, rebuild: bool = False):
       
        self.schema = SCHEMA      
        if rebuild:
            self.rebuild_index()
        self.ix = index.open_dir(index_dir)
        self.parser = QueryParser("content", self.ix.schema)
        
    def rebuild_index(self):
        print("Creating index ...")
        if not INDEX_DIR.exists():
            INDEX_DIR.mkdir()
        ix = index.create_in(INDEX_DIR, self.schema)
        writer = ix.writer()
        for doc_id, doc in enumerate(DATA_DIR.glob("*.srt")):
            content = doc.read_text(encoding="utf-8", errors="ignore")
            
            writer.add_document(
                doc_name=doc.name, 
                content=content,
                doc_id=str(doc_id))
        writer.commit()
        print("Index created successfully.")
        
    def __call__(self, query_str: str) -> List[Dict]:
        with self.ix.searcher() as searcher:
            query_terms = query_str.split()
            query = Or([Term("content", term) for term in query_terms])
            
            results = searcher.search(query, limit=None)
            if len(results) >0:
                search_results = []
                for hit in results:
                    doc_name = hit["doc_name"]
                    content_file_path = DATA_DIR / doc_name
                    content = content_file_path.read_text(encoding="utf-8")
                    result = {
                        "doc_id": hit["doc_id"],
                        "doc_name": hit["doc_name"],
                        "score": hit.score,
                        "content": content,
                        "highlights": hit.highlights("content", text=content)
                    }
                    search_results.append(result)
                return search_results
            else:
                return 
      