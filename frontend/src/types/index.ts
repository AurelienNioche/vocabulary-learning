export interface WordEntry {
  word: string;
  translations: string[];
  kanji?: string;
  example_sentences?: [string, string][];
}

export interface PracticeResult {
  word: string;
  success: boolean;
}

export interface WordDetails {
  word?: string;
  hiragana: string;
  kanji?: string;
  translations: string[];
  example_sentences?: [string, string][];
  progress?: {
    attempts: number;
    successes: number;
    last_seen: string | null;
    review_intervals: number[];
    last_attempt_was_failure: boolean;
    easiness_factor: number;
    interval: number;
  };
}

export interface PracticeStats {
  total_words: number;
  words_started: number;
  words_mastered: number;
  total_attempts: number;
  total_successes: number;
  success_rate: number;
}

export interface User {
  uid: string;
  email: string;
  displayName?: string;
} 