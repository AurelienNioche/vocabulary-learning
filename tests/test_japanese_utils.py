"""Unit tests for Japanese text utilities."""

import unittest
from vocabulary_learning.core.japanese_utils import JapaneseTextConverter

class TestJapaneseTextConverter(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.converter = JapaneseTextConverter()

    def test_romaji_to_hiragana_basic(self):
        """Test basic romaji to hiragana conversion."""
        test_cases = {
            'konnichiwa': 'こんにちわ',
            'ohayou': 'おはよう',
            'sayounara': 'さようなら',
            'arigatou': 'ありがとう'
        }
        for romaji, expected in test_cases.items():
            result = self.converter.romaji_to_hiragana_convert(romaji)
            self.assertEqual(result, expected)

    def test_romaji_to_hiragana_special_cases(self):
        """Test special cases in romaji to hiragana conversion."""
        test_cases = {
            'oo': 'おう',  # Long o
            'ou': 'おう',  # Long o alternative
            'wo': 'を',    # Particle wo
            'n': 'ん'      # Single n
        }
        for romaji, expected in test_cases.items():
            result = self.converter.romaji_to_hiragana_convert(romaji)
            self.assertEqual(result, expected)

    def test_romaji_to_hiragana_compound_sounds(self):
        """Test compound sounds in romaji to hiragana conversion."""
        test_cases = {
            'kya': 'きゃ',
            'shu': 'しゅ',
            'cho': 'ちょ',
            'nya': 'にゃ'
        }
        for romaji, expected in test_cases.items():
            result = self.converter.romaji_to_hiragana_convert(romaji)
            self.assertEqual(result, expected)

    def test_convert_japanese_text_hiragana(self):
        """Test conversion to hiragana from different inputs."""
        # Test hiragana input
        result = self.converter.convert_japanese_text('こんにちは')
        self.assertEqual(result['hiragana'], 'こんにちは')
        
        # Test romaji input
        result = self.converter.convert_japanese_text('konnichiwa')
        self.assertEqual(result['hiragana'], 'こんにちわ')
        
        # Test katakana input
        result = self.converter.convert_japanese_text('コンニチハ')
        self.assertEqual(result['hiragana'], 'こんにちは')

    def test_convert_japanese_text_katakana(self):
        """Test conversion to katakana."""
        result = self.converter.convert_japanese_text('こんにちは')
        self.assertEqual(result['katakana'], 'コンニチハ')

    def test_convert_japanese_text_romaji(self):
        """Test conversion to romaji."""
        result = self.converter.convert_japanese_text('こんにちは')
        self.assertEqual(result['romaji'], 'konnichiha')

    def test_convert_japanese_text_kanji(self):
        """Test handling of kanji in text conversion."""
        # Test with kanji input
        result = self.converter.convert_japanese_text('漢字')
        self.assertIn('kanji', result)
        self.assertEqual(result['hiragana'], 'かんじ')
        
        # Test without kanji input
        result = self.converter.convert_japanese_text('ひらがな')
        self.assertIn('kanji', result)  # Should still have the key
        self.assertEqual(result['hiragana'], 'ひらがな')

    def test_error_handling(self):
        """Test error handling in text conversion."""
        # Test with invalid input
        result = self.converter.convert_japanese_text('123')
        self.assertIsInstance(result, dict)
        self.assertIn('hiragana', result)
        self.assertIn('katakana', result)
        self.assertIn('romaji', result)
        self.assertIn('kanji', result)

    def test_suggest_translation(self):
        """Test translation suggestion functionality."""
        # Note: This test might fail if Google Translate is unavailable
        translation = self.converter.suggest_translation('こんにちは', 'ja', 'fr')
        self.assertIsInstance(translation, (str, type(None)))

if __name__ == '__main__':
    unittest.main()
