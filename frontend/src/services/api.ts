import axios from 'axios';
import { WordEntry, PracticeResult } from '../types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const vocabularyApi = {
  getAll: () => api.get<string[]>('/vocabulary'),
  getWord: (word: string) => api.get(`/vocabulary/${word}`),
  addWord: (wordEntry: WordEntry) => api.post('/vocabulary', wordEntry),
  updateWord: (word: string, wordEntry: WordEntry) => api.put(`/vocabulary/${word}`, wordEntry),
  deleteWord: (word: string) => api.delete(`/vocabulary/${word}`),
  search: (query: string) => api.get<string[]>(`/vocabulary/search/${query}`),
};

export const practiceApi = {
  getWords: (numWords: number = 10) => api.get<string[]>(`/practice/words?num_words=${numWords}`),
  getWord: (word: string) => api.get(`/vocabulary/${word}`),
  submitResult: (result: PracticeResult) => api.post('/practice/result', result),
  getStats: () => api.get('/practice/stats'),
  getSuggestions: (word: string, numSuggestions: number = 3) =>
    api.get<[string, number][]>(`/practice/suggestions/${word}?num_suggestions=${numSuggestions}`),
};

export default api; 