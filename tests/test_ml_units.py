from ml.models.stt import SpeechToText
from ml.utils.text import chunk_text, clean_text


def test_clean_text_collapses_whitespace():
    assert clean_text("  hello\n\nworld\t ") == "hello world"


def test_chunk_text_splits_by_word_count():
    text = "one two three four five"
    assert chunk_text(text, chunk_size=2) == ["one two", "three four", "five"]


def test_pause_based_speaker_labels_increment_after_long_pause():
    stt = SpeechToText()
    segments = [
        {"start": 0.0, "end": 1.0, "text": "Welcome"},
        {"start": 1.4, "end": 2.0, "text": "Still the host"},
        {"start": 4.0, "end": 5.0, "text": "A new speaker"},
    ]

    labeled = stt._assign_speakers(segments)

    assert [segment["speaker"] for segment in labeled] == [
        "HOST",
        "HOST",
        "GUEST_1",
    ]
    assert labeled[2]["pause_before"] == 2.0
