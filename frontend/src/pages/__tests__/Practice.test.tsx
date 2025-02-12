import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { Mock } from 'vitest';
import Practice from '../Practice';
import { practiceApi } from '../../services/api';
import type { WordDetails } from '../../types';

// Mock the API calls
vi.mock('../../services/api', () => ({
  practiceApi: {
    getWords: vi.fn(),
    getWord: vi.fn(),
    submitResult: vi.fn(),
  },
}));

describe('Practice Component', () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  const mockWords = ['word_000001', 'word_000002'];
  const mockWordDetails: WordDetails = {
    hiragana: 'こんにちは',
    kanji: '今日は',
    translations: ['bonjour', 'salut'],
    example_sentences: [['こんにちは、元気ですか？', 'Bonjour, comment allez-vous ?']],
  };

  beforeEach(() => {
    // Reset all mocks before each test
    vi.clearAllMocks();
    
    // Setup default mock responses
    (practiceApi.getWords as Mock).mockResolvedValue({ data: mockWords });
    (practiceApi.getWord as Mock).mockResolvedValue({ data: mockWordDetails });
    (practiceApi.submitResult as Mock).mockResolvedValue({ data: { status: 'success' } });
  });

  it('renders loading state initially', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <Practice />
      </QueryClientProvider>
    );
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('displays word and handles correct answer', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <Practice />
      </QueryClientProvider>
    );

    // Wait for the word to be displayed
    await waitFor(() => {
      expect(screen.getByText('こんにちは')).toBeInTheDocument();
    });

    // Enter correct answer
    const input = screen.getByLabelText(/your answer/i);
    fireEvent.change(input, { target: { value: 'bonjour' } });

    // Submit answer
    const submitButton = screen.getByRole('button', { name: /check/i });
    fireEvent.click(submitButton);

    // Verify API call
    await waitFor(() => {
      expect(practiceApi.submitResult).toHaveBeenCalledWith({
        word: mockWords[0],
        success: true,
      });
    });
  });

  it('handles incorrect answer', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <Practice />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('こんにちは')).toBeInTheDocument();
    });

    // Enter wrong answer
    const input = screen.getByLabelText(/your answer/i);
    fireEvent.change(input, { target: { value: 'wrong' } });

    // Submit answer
    const submitButton = screen.getByRole('button', { name: /check/i });
    fireEvent.click(submitButton);

    // Verify error message and API call
    await waitFor(() => {
      expect(screen.getByText(/incorrect/i)).toBeInTheDocument();
      expect(practiceApi.submitResult).toHaveBeenCalledWith({
        word: mockWords[0],
        success: false,
      });
    });
  });

  it('shows example sentence when requested', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <Practice />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('こんにちは')).toBeInTheDocument();
    });

    // Click show example button
    const exampleButton = screen.getByRole('button', { name: /show example/i });
    fireEvent.click(exampleButton);

    // Verify example sentence is displayed
    expect(screen.getByText('こんにちは、元気ですか？')).toBeInTheDocument();
    expect(screen.getByText('Bonjour, comment allez-vous ?')).toBeInTheDocument();
  });

  it('handles "Show Answer" button', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <Practice />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('こんにちは')).toBeInTheDocument();
    });

    // Click show answer button
    const showAnswerButton = screen.getByRole('button', { name: /show answer/i });
    fireEvent.click(showAnswerButton);

    // Wait for the answer to be displayed
    await waitFor(() => {
      const answerText = screen.getByText((content) => {
        return content.includes('bonjour') && content.includes('salut');
      });
      expect(answerText).toBeInTheDocument();
    });

    // Verify API call for failed attempt
    expect(practiceApi.submitResult).toHaveBeenCalledWith({
      word: mockWords[0],
      success: false,
    });
  });

  it('handles API errors gracefully', async () => {
    // Mock API error
    (practiceApi.getWords as Mock).mockRejectedValue(new Error('API Error'));

    render(
      <QueryClientProvider client={queryClient}>
        <Practice />
      </QueryClientProvider>
    );

    // Verify error message is displayed
    await waitFor(() => {
      expect(screen.getByText(/error loading practice data/i)).toBeInTheDocument();
    });
  });

  it('handles empty vocabulary', async () => {
    // Mock empty word list
    (practiceApi.getWords as Mock).mockResolvedValue({ data: [] });

    render(
      <QueryClientProvider client={queryClient}>
        <Practice />
      </QueryClientProvider>
    );

    // Verify message for empty vocabulary
    await waitFor(() => {
      expect(screen.getByText(/no words available/i)).toBeInTheDocument();
    });
  });
}); 