from backend.app.documents.ingestion import ingest_policy_document
from backend.app.models.policy import PolicyDocument
from backend.app.services.retrieval import BM25Index, retrieve_sections, tokenize


def _policy_with_document(db_session, text):
    policy = PolicyDocument(title="Retrieval Test Policy")
    db_session.add(policy)
    db_session.commit()
    ingest_policy_document(db_session, policy.id, "p.txt", text.encode("utf-8"))
    return policy


# ---- tokenization -------------------------------------------------------------

def test_tokenize_lowercases_and_splits():
    assert tokenize("Hello, World! Transparency-123") == ["hello", "world", "transparency", "123"]


# ---- BM25 core ------------------------------------------------------------

def test_bm25_ranks_more_relevant_document_higher():
    index = BM25Index([
        (1, "transparency and accountability in government"),
        (2, "funding for new electric buses and transit"),
    ])
    scores = dict(index.score_all("transparency accountability"))
    assert scores[1] > scores[2]


def test_bm25_zero_score_for_no_term_overlap():
    index = BM25Index([(1, "completely unrelated content about gardening")])
    scores = dict(index.score_all("transparency government"))
    assert scores[1] == 0.0


def test_bm25_handles_empty_index():
    index = BM25Index([])
    assert index.score_all("anything") == []


# ---- section-level retrieval, independent of stance -------------------------

def test_retrieve_sections_returns_relevant_sections_ranked(db_session):
    policy = _policy_with_document(
        db_session,
        "Section 1. Transparency\nThe government commits to full transparency in all operations.\n\n"
        "Section 2. Budget\nThe annual budget allocation is described here with funding details.",
    )
    results = retrieve_sections(db_session, policy.id, "transparency government operations", top_k=5)
    assert len(results) >= 1
    assert results[0].section_label == "Section 1. Transparency"
    assert results[0].score > 0


def test_retrieve_sections_no_match_returns_empty(db_session):
    policy = _policy_with_document(db_session, "Section 1. Budget\nFunding details about buses.")
    results = retrieve_sections(db_session, policy.id, "xyzzy nonexistent query term qwerty")
    assert results == []


def test_retrieve_sections_respects_top_k(db_session):
    text = "\n\n".join(f"Section {i}. Topic\nTransparency content number {i}." for i in range(10))
    policy = _policy_with_document(db_session, text)
    results = retrieve_sections(db_session, policy.id, "transparency content", top_k=3)
    assert len(results) <= 3


def test_retrieve_sections_for_policy_with_no_document_returns_empty(db_session):
    policy = PolicyDocument(title="No document yet")
    db_session.add(policy)
    db_session.commit()
    results = retrieve_sections(db_session, policy.id, "anything")
    assert results == []


def test_retrieval_result_carries_provenance(db_session):
    policy = _policy_with_document(db_session, "Section 1. Transparency\nFull transparency commitment text.")
    results = retrieve_sections(db_session, policy.id, "transparency")
    assert len(results) == 1
    r = results[0]
    assert r.method == "bm25"
    assert r.query == "transparency"
    assert r.policy_document_id == policy.id
    assert r.policy_document_version_id is not None
    assert r.retrieved_at is not None


def test_retrieval_never_imports_stance_models():
    """Static guard: the retrieval module must not IMPORT anything from
    the stance models, enforcing independence at the module-dependency
    level, not just by convention. Checked via the AST's import
    statements specifically (not a raw substring search over the file,
    which would also match the module's own docstring explaining this
    very principle in prose)."""
    import ast

    import backend.app.services.retrieval as retrieval_module

    tree = ast.parse(open(retrieval_module.__file__, encoding="utf-8").read())
    imported_modules = set()
    imported_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)
            imported_names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)

    assert not any("stance" in m for m in imported_modules)
    assert "StancePrediction" not in imported_names
