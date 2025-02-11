import pytest
from vocab_learner.japanese_utils import JapaneseTextConverter

def test_japanese_conversion():
    converter = JapaneseTextConverter()
    result = converter.convert_text("おはよう")
    
    assert 'hiragana' in result
    assert 'katakana' in result
    assert 'romaji' in result
    assert result['hiragana'] == 'おはよう'
    assert result['romaji'] == 'ohayou'

def test_invalid_input():
    converter = JapaneseTextConverter()
    with pytest.raises(ValueError):
        converter.convert_text(None)
