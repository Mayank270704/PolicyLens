import pytest

from backend.app.ml_interfaces import MLComponentNotImplemented
from backend.app.ml_interfaces.concern_grouping import NotYetConfiguredConcernGrouper
from backend.app.ml_interfaces.embedding_provider import NotYetConfiguredEmbeddingProvider
from backend.app.ml_interfaces.representative_selector import CentroidSimilarityRepresentativeSelector
from backend.app.ml_interfaces.stance_classifier import NotYetTrainedStanceClassifier
from backend.app.ml_interfaces.summarizer import ExtractiveSummarizer, NotYetConfiguredAbstractiveSummarizer


# ---- placeholders raise explicitly, never fabricate a result ---------------

def test_stance_classifier_placeholder_raises_not_fabricates():
    clf = NotYetTrainedStanceClassifier()
    with pytest.raises(MLComponentNotImplemented):
        clf.predict("some comment", "ctx", "sec")


def test_stance_classifier_batch_raises_too():
    clf = NotYetTrainedStanceClassifier()
    with pytest.raises(MLComponentNotImplemented):
        clf.predict_batch([("a", "ctx", "sec"), ("b", "ctx", "sec")])


def test_embedding_provider_placeholder_raises():
    provider = NotYetConfiguredEmbeddingProvider()
    with pytest.raises(MLComponentNotImplemented):
        provider.embed(["some text"])


def test_concern_grouper_placeholder_raises():
    grouper = NotYetConfiguredConcernGrouper()
    with pytest.raises(MLComponentNotImplemented):
        grouper.fit_predict([1, 2], [[0.1, 0.2], [0.3, 0.4]])


def test_abstractive_summarizer_placeholder_raises():
    summarizer = NotYetConfiguredAbstractiveSummarizer()
    with pytest.raises(MLComponentNotImplemented):
        summarizer.summarize({1: "text"})


# ---- real, implemented components ------------------------------------------

def test_extractive_summarizer_produces_full_evidence_coverage():
    summarizer = ExtractiveSummarizer()
    result = summarizer.summarize({1: "First comment.", 2: "Second comment."})
    assert result.method == "extractive"
    assert set(result.evidence_comment_ids) == {1, 2}
    assert "First comment." in result.text
    assert "Second comment." in result.text


def test_extractive_summarizer_empty_input():
    summarizer = ExtractiveSummarizer()
    result = summarizer.summarize({})
    assert result.evidence_comment_ids == []
    assert result.text == ""


def test_representative_selector_picks_closest_to_centroid():
    selector = CentroidSimilarityRepresentativeSelector()
    embeddings = {
        1: [1.0, 0.0],
        2: [0.99, 0.01],   # very close to comment 1 -- near the centroid
        3: [-1.0, 0.5],    # an outlier, further from the centroid
    }
    result = selector.select([1, 2, 3], embeddings, top_n=2)
    assert len(result) == 2
    assert result[0].rank == 1
    # the outlier (id 3) should not be ranked first
    assert result[0].comment_id != 3


def test_representative_selector_respects_top_n():
    selector = CentroidSimilarityRepresentativeSelector()
    embeddings = {i: [float(i), 1.0] for i in range(10)}
    result = selector.select(list(range(10)), embeddings, top_n=3)
    assert len(result) == 3


def test_representative_selector_empty_group():
    selector = CentroidSimilarityRepresentativeSelector()
    assert selector.select([], {}, top_n=5) == []
