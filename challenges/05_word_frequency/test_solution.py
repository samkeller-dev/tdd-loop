from solution import word_freq


def test_empty():
    assert word_freq("") == {}


def test_single_word():
    assert word_freq("hello") == {"hello": 1}


def test_case_insensitive():
    assert word_freq("Hello hello HELLO") == {"hello": 3}


def test_punctuation_stripped():
    assert word_freq("The quick brown fox.") == {
        "the": 1, "quick": 1, "brown": 1, "fox": 1,
    }


def test_internal_apostrophe_kept():
    assert word_freq("Don't stop. Don't!") == {"don't": 2, "stop": 1}


def test_repeated_simple():
    assert word_freq("a b a c b a") == {"a": 3, "b": 2, "c": 1}


def test_lone_punctuation_excluded():
    # ',' on its own is not a word.
    result = word_freq("hi , there")
    assert result == {"hi": 1, "there": 1}


def test_multiple_whitespace():
    assert word_freq("a  \t b\n\nc") == {"a": 1, "b": 1, "c": 1}
