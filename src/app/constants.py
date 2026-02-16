from whoosh.fields import Schema, TEXT, ID


SCHEMA = Schema(
    doc_id=ID(stored=True, unique=True),
    content=TEXT(),
    doc_name=TEXT(stored=True)
)
    