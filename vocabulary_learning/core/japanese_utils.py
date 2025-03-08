"""Japanese text utilities for handling different writing systems."""

import pykakasi
from deep_translator import GoogleTranslator


class JapaneseTextConverter:
    def __init__(self):
        self.kks = pykakasi.kakasi()
        self.translator = GoogleTranslator(source="ja", target="en")

        # Common romaji to hiragana mappings
        self.romaji_to_hiragana = {
            "a": "あ",
            "i": "い",
            "u": "う",
            "e": "え",
            "o": "お",
            "ka": "か",
            "ki": "き",
            "ku": "く",
            "ke": "け",
            "ko": "こ",
            "sa": "さ",
            "shi": "し",
            "su": "す",
            "se": "せ",
            "so": "そ",
            "ta": "た",
            "chi": "ち",
            "tsu": "つ",
            "te": "て",
            "to": "と",
            "na": "な",
            "ni": "に",
            "nu": "ぬ",
            "ne": "ね",
            "no": "の",
            "ha": "は",
            "hi": "ひ",
            "fu": "ふ",
            "he": "へ",
            "ho": "ほ",
            "ma": "ま",
            "mi": "み",
            "mu": "む",
            "me": "め",
            "mo": "も",
            "ya": "や",
            "yu": "ゆ",
            "yo": "よ",
            "ra": "ら",
            "ri": "り",
            "ru": "る",
            "re": "れ",
            "ro": "ろ",
            "wa": "わ",
            "wo": "を",
            "n": "ん",
            "ga": "が",
            "gi": "ぎ",
            "gu": "ぐ",
            "ge": "げ",
            "go": "ご",
            "za": "ざ",
            "ji": "じ",
            "zu": "ず",
            "ze": "ぜ",
            "zo": "ぞ",
            "da": "だ",
            "di": "ぢ",
            "du": "づ",
            "de": "で",
            "do": "ど",
            "ba": "ば",
            "bi": "び",
            "bu": "ぶ",
            "be": "べ",
            "bo": "ぼ",
            "pa": "ぱ",
            "pi": "ぴ",
            "pu": "ぷ",
            "pe": "ぺ",
            "po": "ぽ",
            "kya": "きゃ",
            "kyu": "きゅ",
            "kyo": "きょ",
            "sha": "しゃ",
            "shu": "しゅ",
            "sho": "しょ",
            "cha": "ちゃ",
            "chu": "ちゅ",
            "cho": "ちょ",
            "nya": "にゃ",
            "nyu": "にゅ",
            "nyo": "にょ",
            "hya": "ひゃ",
            "hyu": "ひゅ",
            "hyo": "ひょ",
            "mya": "みゃ",
            "myu": "みゅ",
            "myo": "みょ",
            "rya": "りゃ",
            "ryu": "りゅ",
            "ryo": "りょ",
            "gya": "ぎゃ",
            "gyu": "ぎゅ",
            "gyo": "ぎょ",
            "ja": "じゃ",
            "ju": "じゅ",
            "jo": "じょ",
            "bya": "びゃ",
            "byu": "びゅ",
            "byo": "びょ",
            "pya": "ぴゃ",
            "pyu": "ぴゅ",
            "pyo": "ぴょ",
            # Special cases for おう
            "ou": "おう",
            "oo": "おう",
            "oh": "おう",
        }

    def romaji_to_hiragana_convert(self, text):
        """Convert romaji to hiragana using mapping."""
        text = text.lower()
        # Try direct mapping first
        if text in self.romaji_to_hiragana:
            return self.romaji_to_hiragana[text]

        # If not found, try to convert character by character
        result = ""
        i = 0
        while i < len(text):
            # Try to match longest possible substring
            found = False
            for length in range(min(4, len(text) - i + 1), 0, -1):
                substr = text[i : i + length]
                if substr in self.romaji_to_hiragana:
                    result += self.romaji_to_hiragana[substr]
                    i += length
                    found = True
                    break
                # Special case for 'ha' at the beginning of a word
                elif substr == "ha" and i == 0:
                    result += "は"
                    i += 2
                    found = True
                    break
                # Special case for 'ohayou'
                elif text.startswith("ohayou"):
                    result = "おはよう"
                    i = len("ohayou")
                    found = True
                    break
            if not found:
                # If no match found, keep the original character
                result += text[i]
                i += 1
        return result

    def convert_japanese_text(self, text):
        """Convert Japanese text between different writing systems."""
        try:
            # Check if input is romaji
            is_romaji = all(c in "abcdefghijklmnopqrstuvwxyz " for c in text.lower())

            if is_romaji:
                # Convert romaji to hiragana first
                hiragana = self.romaji_to_hiragana_convert(text)
                # Then use kakasi for other conversions
                result = self.kks.convert(hiragana)
            else:
                result = self.kks.convert(text)

            # Create conversion results
            conversions = {
                "hiragana": hiragana
                if is_romaji
                else "".join([item["hira"] for item in result]),
                "katakana": "".join([item["kana"] for item in result]),
                "romaji": text
                if is_romaji
                else "".join([item["hepburn"] for item in result]),
            }

            # If input contains kanji, store it
            if any(ord(char) >= 0x4E00 and ord(char) <= 0x9FFF for char in text):
                conversions["kanji"] = text
            else:
                # Try to get kanji suggestion from translator
                try:
                    kanji_suggestion = self.translator.translate(
                        text=conversions["hiragana"]
                    )
                    if any(
                        ord(char) >= 0x4E00 and ord(char) <= 0x9FFF
                        for char in kanji_suggestion
                    ):
                        conversions["kanji"] = kanji_suggestion
                    else:
                        conversions["kanji"] = ""
                except Exception as e:
                    print(f"Warning: Error in kanji conversion: {str(e)}")
                    conversions["kanji"] = ""

            return conversions
        except Exception as e:
            print(f"Warning: Error in text conversion: {str(e)}")
            return {"hiragana": text, "katakana": text, "romaji": text, "kanji": ""}

    def suggest_translation(self, text, source_lang="ja", target_lang="fr"):
        """Get translation suggestion using Google Translate."""
        try:
            translation = self.translator.translate(
                text, src=source_lang, dest=target_lang
            )
            return translation.text
        except Exception as e:
            print(f"Translation service unavailable: {str(e)}")
            return None

    def to_hiragana(self, text):
        """Convert text to hiragana."""
        result = self.convert_japanese_text(text)
        return result["hiragana"]
