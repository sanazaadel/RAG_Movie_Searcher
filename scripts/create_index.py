from whoosh import index
from whoosh.fields import Schema, TEXT, ID
from whoosh.analysis import StemmingAnalyzer
from src import INDEX_DIR, DATA_DIR
from src.app.constants import SCHEMA
from argparse import ArgumentParser

if __name__ == "__main__":
    # Define the schema 
        ## Command-line argument parsing for index rebuilding
    parser = ArgumentParser()
    parser.add_argument("--rebuild", action="store_true", help="Rebuild the index")
    args = parser.parse_args()
    
    schema = SCHEMA

    # Create the index directory if it doesn't exist
    if not index.exists_in(INDEX_DIR):
        print(f"Creating index ...")
        if not INDEX_DIR.exists():
            INDEX_DIR.mkdir()
        ix = index.create_in(INDEX_DIR, schema)
    else:
        print("Opening existing index ...")
        ix = index.open_dir(INDEX_DIR)
        
    writer = ix.writer()
    for doc_id, doc in enumerate(DATA_DIR.glob("*.srt")):
        content = doc.read_text(encoding="utf-8", errors="ignore")
       
        writer.add_document(
            doc_name=doc.name, 
            content=content,
            doc_id=str(doc_id))
    writer.commit()
    