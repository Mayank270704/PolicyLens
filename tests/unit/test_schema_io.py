"""CSV round-trip edge cases the generation script's own fixtures didn't
need to cover: embedded newlines/quotes/commas in comment_text (known to
occur in the real corpus, up to 7,229 chars), and atomic-write crash
safety (no partial file left behind)."""
from scripts.annotation import schema
from tests.unit.test_validate import make_row


def test_round_trip_preserves_embedded_newline_in_comment_text(tmp_path):
    path = tmp_path / "batch.csv"
    text = "Line one of a long comment.\nLine two, after a real newline.\nLine three."
    rows = [make_row(comment_id="PL-1", comment_text=text)]
    schema.write_rows_atomic(path, rows, schema.REQUIRED_COLUMNS)

    read_back = schema.read_rows(path)
    assert read_back[0]["comment_text"] == text


def test_round_trip_preserves_embedded_quotes_and_commas(tmp_path):
    path = tmp_path / "batch.csv"
    text = 'She said, "this policy, as written, is unworkable" -- and I agree.'
    rows = [make_row(comment_id="PL-1", comment_text=text)]
    schema.write_rows_atomic(path, rows, schema.REQUIRED_COLUMNS)

    read_back = schema.read_rows(path)
    assert read_back[0]["comment_text"] == text


def test_round_trip_preserves_very_long_text(tmp_path):
    path = tmp_path / "batch.csv"
    text = "word " * 1200  # longer than the corpus's longest observed comment
    rows = [make_row(comment_id="PL-1", comment_text=text)]
    schema.write_rows_atomic(path, rows, schema.REQUIRED_COLUMNS)

    read_back = schema.read_rows(path)
    assert read_back[0]["comment_text"] == text


def test_atomic_write_leaves_no_tmp_file_behind(tmp_path):
    path = tmp_path / "batch.csv"
    rows = [make_row(comment_id="PL-1")]
    schema.write_rows_atomic(path, rows, schema.REQUIRED_COLUMNS)

    tmp_sibling = path.with_name(path.name + ".tmp")
    assert path.exists()
    assert not tmp_sibling.exists()


def test_atomic_write_fully_replaces_prior_content_not_appends(tmp_path):
    path = tmp_path / "batch.csv"
    schema.write_rows_atomic(path, [make_row(comment_id="PL-1")], schema.REQUIRED_COLUMNS)
    schema.write_rows_atomic(path, [make_row(comment_id="PL-2")], schema.REQUIRED_COLUMNS)

    rows = schema.read_rows(path)
    assert len(rows) == 1
    assert rows[0]["comment_id"] == "PL-2"


def test_sha256_file_is_deterministic(tmp_path):
    path = tmp_path / "batch.csv"
    schema.write_rows_atomic(path, [make_row(comment_id="PL-1")], schema.REQUIRED_COLUMNS)
    h1 = schema.sha256_file(path)
    h2 = schema.sha256_file(path)
    assert h1 == h2
    assert len(h1) == 64
