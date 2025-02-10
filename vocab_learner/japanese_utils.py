from typing import Dict, Optional
import pykakasi
from googletrans import Translator

class JapaneseTextConverter:
    """Handles Japanese text conversion between different writing systems."""
    
    def __init__(self) -> None:
        self.kks = pykakasi.kakasi()
        self.translator = Translator()
        
    def convert_text(self, text: str) -> Dict[str, str]:
        """
        Convert Japanese text between different writing systems.
        
        Args:
            text: Input text in any Japanese writing system
            
        Returns:
            Dict containing text in different writing systems
        """
        try:
            result = self.kks.convert(text)
            return {
                'hiragana': ''.join([item['hira'] for item in result]),
                'katakana': ''.join([item['kana'] for item in result]),
                'romaji': ''.join([item['hepburn'] for item in result])
            }
        except Exception as e:
            raise ValueError(f"Error converting text: {str(e)}")
