import re
import time
from typing import Dict, List

import streamlit as st

from src import DATA_DIR, INDEX_DIR
from src.app.llm import call_llm
from src.app.search import SearchEngine
from src.app.srt_tools import clean_srt


STARTER_QUESTIONS = [
    "What is happening in this scene?",
    "Summarize what’s going on right now.",
    "What problem are the characters dealing with?",
    "What are the characters arguing about?",
    "What decision is being discussed here?",
    "What happens next in this scene?",
    "Why is someone upset here?",
    "What is the mood of this moment?",
]


def pretty_title(filename: str) -> str:
    """Turn 'Seven.Pounds.srt' into 'Seven Pounds'."""
    return filename.replace(".srt", "").replace(".", " ").replace("_", " ").strip()


def split_srt_into_blocks(srt_text: str) -> List[str]:
    """SRT blocks are separated by blank lines."""
    blocks = re.split(r"\n\s*\n", (srt_text or "").strip())
    return [b.strip() for b in blocks if b.strip()]


def pick_keywords(question: str) -> List[str]:
    """
    Keep meaningful keywords from the question.
    """
    words = [w.lower() for w in re.findall(r"[a-zA-Z']+", question)]
    keys = [w for w in words if len(w) >= 4]

    # a few short-but-important words
    for w in ("car", "gun", "war", "cop", "dad", "mom"):
        if w in words:
            keys.append(w)

    # de-dup (preserve order)
    seen = set()
    out = []
    for k in keys:
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out


def narrow_to_named_movie(hits: List[Dict], question: str) -> List[Dict]:
    """
    If the user included a movie name that matches a filename,
    keep only hits from that movie.
    """
    q = question.lower()

    for h in hits:
        movie = pretty_title(h["doc_name"]).lower()
        movie = re.sub(r"\s+", " ", movie).strip()
        if movie and movie in q:
            return [x for x in hits if x["doc_name"] == h["doc_name"]]

    return hits


def build_context_from_movie(movie_file: str, question: str, max_blocks: int = 8) -> str:
    """
    Pull subtitle blocks from the *actual* SRT file that match the question keywords.
    
    """
    raw = (DATA_DIR / movie_file).read_text(encoding="utf-8", errors="ignore")

    # Clean tags, keep structure (timestamps/indices still there unless removed)
    cleaned = clean_srt(
        raw,
        remove_tags=True,
        remove_index_lines=False,
        remove_timestamps=False,
    )

    blocks = split_srt_into_blocks(cleaned)
    keys = pick_keywords(question)

    chosen = []
    for b in blocks:
        low = b.lower()
        if any(k in low for k in keys):
            chosen.append(b)
            if len(chosen) >= max_blocks:
                break

    return "\n\n---\n\n".join(chosen)


def build_llm_context(hits: List[Dict], question: str, max_chars: int = 3500) -> str:
    """
    Try context from top movie file; fall back to Whoosh highlights if nothing matches.
    """
    top_movie = hits[0]["doc_name"]

    ctx = build_context_from_movie(top_movie, question, max_blocks=8)
    if ctx.strip():
        return ctx[:max_chars]

    # fallback: use Whoosh highlights (strip HTML)
    same_movie = [h for h in hits if h["doc_name"] == top_movie][:3]
    snippets = []
    for h in same_movie:
        s = h.get("highlights", "") or ""
        s = re.sub(r"<[^>]+>", "", s)
        s = re.sub(r"\s+", " ", s).strip()
        if s:
            snippets.append(s)

    return ("\n\n---\n\n".join(snippets))[:max_chars]


def render_starter_buttons():
    st.subheader("Try one of these")
    cols = st.columns(2)
    for i, q in enumerate(STARTER_QUESTIONS):
        if cols[i % 2].button(q, key=f"starter_{i}"):
            st.session_state.query = q
            st.rerun()


def render_suggestions_for_top_movie(top_movie_file: str):
    movie = pretty_title(top_movie_file)

    st.subheader("Suggested questions")
    st.caption(f"Top match: **{movie}**")

    movie_suggestions = [
        f"In {movie}, what is happening in this scene?",
        f"In {movie}, what are the characters arguing about?",
        f"In {movie}, what problem are they trying to solve?",
        f"In {movie}, what happens next in this scene?",
    ]

    cols = st.columns(2)
    all_qs = movie_suggestions + STARTER_QUESTIONS

    for i, q in enumerate(all_qs):
        if cols[i % 2].button(q, key=f"suggest_{i}"):
            st.session_state.query = q
            st.rerun()


def main():
    st.title("Movie Search")

    if "query" not in st.session_state:
        st.session_state.query = ""

    user_query = st.text_input("Enter your search query:", value=st.session_state.query)

    search_engine = SearchEngine(INDEX_DIR)

    if st.sidebar.button("Rebuild Index"):
        search_engine.rebuild_index()
        st.sidebar.success("Index rebuilt successfully.")

    
    if not user_query.strip():
        render_starter_buttons()
        st.info("Not sure what to ask? You can also search for a word like “priest”, “argument”, or “car”.")
        return

    with st.spinner("Searching..."):
        time.sleep(0.25)
        hits = search_engine(user_query)

    if not hits:
        st.write("No results found.")
        render_starter_buttons()
        if st.button("Clear query"):
            st.session_state.query = ""
            st.rerun()
        return

    # If user included a movie name, lock to that movie
    hits = narrow_to_named_movie(hits, user_query)

    # Suggestions + "what to ask" based on top match
    top_movie_file = hits[0]["doc_name"]
    
    # Sidebar: show top 3 hits
    for h in hits[:3]:
        st.sidebar.write(f"**{h['doc_name']}** (Score: {h['score']:.2f})")
        st.sidebar.markdown(h.get("highlights", ""), unsafe_allow_html=True)

        full_text = (DATA_DIR / h["doc_name"]).read_text(encoding="utf-8", errors="ignore")
        st.sidebar.expander("Full Content", expanded=False).write(full_text)
        st.sidebar.write("---")

    # Let the user know what we’re answering from
    st.caption(f"Answering based on: **{pretty_title(top_movie_file)}**")

    # LLM context + answer
    context = build_llm_context(hits, user_query)

    prompt = (
        "You are given subtitle blocks from a movie.\n\n"
        f"SUBTITLES:\n{context}\n\n"
        f"QUESTION:\n{user_query.strip()}\n\n"
        "Answer using only what is supported by the subtitles. "
        "If the subtitles don't contain enough information, say: "
        "\"Not enough information in the subtitles shown.\""
    )

    model_name = "gpt-3.5-turbo"
    answer = call_llm(model_name, prompt, max_tokens=400)
    st.write(answer)
    render_suggestions_for_top_movie(top_movie_file)

    if st.button("Clear query"):
        st.session_state.query = ""
        st.rerun()


if __name__ == "__main__":
    main()
