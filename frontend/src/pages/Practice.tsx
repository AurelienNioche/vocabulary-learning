import { useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  TextField,
  Typography,
  Alert,
  CircularProgress,
  Stack,
} from '@mui/material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { practiceApi } from '../services/api';
import { PracticeResult, WordDetails } from '../types';

function Practice() {
  const [answer, setAnswer] = useState('');
  const [showAnswer, setShowAnswer] = useState(false);
  const [showExample, setShowExample] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const { data: words = [], isLoading: isLoadingWords, isError: isWordsError } = useQuery<string[]>({
    queryKey: ['practice-words'],
    queryFn: async () => {
      const response = await practiceApi.getWords();
      return response.data;
    },
  });

  const [currentWordIndex, setCurrentWordIndex] = useState(0);
  const currentWord = words[currentWordIndex];

  const { data: wordDetails, isLoading: isLoadingWord } = useQuery<WordDetails>({
    queryKey: ['word-details', currentWord],
    queryFn: async () => {
      if (!currentWord) throw new Error('No word selected');
      const response = await practiceApi.getWord(currentWord);
      return response.data;
    },
    enabled: !!currentWord,
  });

  const submitMutation = useMutation({
    mutationFn: (result: PracticeResult) => practiceApi.submitResult(result),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['practice-stats'] });
    },
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentWord || !wordDetails) return;

    const isCorrect = wordDetails.translations.some(
      (t: string) => t.toLowerCase().trim() === answer.toLowerCase().trim()
    );

    try {
      await submitMutation.mutateAsync({
        word: currentWord,
        success: isCorrect,
      });

      if (isCorrect) {
        setShowAnswer(true);
        setError(null);
        handleNextWord();
      } else {
        setError('Incorrect. Try again or show the answer.');
      }
    } catch (error) {
      console.error('Failed to submit answer:', error);
      setError('Failed to submit answer. Please try again.');
    }
  };

  const handleShowAnswer = async () => {
    if (!currentWord) return;

    try {
      await submitMutation.mutateAsync({
        word: currentWord,
        success: false,
      });
      setShowAnswer(true);
      setShowExample(true);
    } catch (error) {
      console.error('Failed to show answer:', error);
      setError('Failed to submit answer. Please try again.');
    }
  };

  const handleNextWord = () => {
    if (currentWordIndex < words.length - 1) {
      setCurrentWordIndex((prev) => prev + 1);
    } else {
      setCurrentWordIndex(0);
    }
    setAnswer('');
    setShowAnswer(false);
    setShowExample(false);
    setError(null);
  };

  if (isLoadingWords || (isLoadingWord && currentWord)) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (isWordsError) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <Alert severity="error">
          Error loading practice data. Please try again later.
        </Alert>
      </Box>
    );
  }

  if (!words.length) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <Alert severity="info">
          No words available for practice. Please add some words first.
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3 }}>
        Practice
      </Typography>

      <Card sx={{ maxWidth: 600, mx: 'auto' }}>
        <CardContent>
          {wordDetails && (
            <Stack spacing={2}>
              <Typography variant="h5" align="center">
                {wordDetails.hiragana}
              </Typography>
              {wordDetails.kanji && (
                <Typography variant="subtitle1" color="text.secondary" align="center">
                  {wordDetails.kanji}
                </Typography>
              )}

              <Box component="form" onSubmit={handleSubmit}>
                <TextField
                  fullWidth
                  label="Your answer (French)"
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  disabled={showAnswer}
                  autoFocus
                  sx={{ mb: 2 }}
                />

                {error && !showAnswer && (
                  <Alert severity="error" sx={{ mb: 2 }}>
                    {error}
                  </Alert>
                )}

                {showAnswer && (
                  <>
                    <Alert severity="info" sx={{ mb: 2 }}>
                      <Typography variant="subtitle1" gutterBottom>
                        Correct answer: {wordDetails.translations.join(' / ')}
                      </Typography>
                      {showExample && wordDetails.example_sentences?.[0] && (
                        <Box sx={{ mt: 2 }}>
                          <Typography variant="subtitle2" gutterBottom>Example:</Typography>
                          <Typography paragraph>{wordDetails.example_sentences[0][0]}</Typography>
                          <Typography>{wordDetails.example_sentences[0][1]}</Typography>
                        </Box>
                      )}
                    </Alert>
                    <Button
                      fullWidth
                      variant="contained"
                      onClick={handleNextWord}
                    >
                      Next Word
                    </Button>
                  </>
                )}

                {!showAnswer && (
                  <Stack direction="row" spacing={2}>
                    <Button
                      variant="contained"
                      color="primary"
                      type="submit"
                      fullWidth
                    >
                      Check
                    </Button>
                    <Button
                      variant="outlined"
                      color="secondary"
                      onClick={handleShowAnswer}
                      fullWidth
                    >
                      Show Answer
                    </Button>
                    {wordDetails.example_sentences?.[0] && (
                      <Button
                        variant="outlined"
                        onClick={() => setShowExample(!showExample)}
                        fullWidth
                      >
                        {showExample ? 'Hide Example' : 'Show Example'}
                      </Button>
                    )}
                  </Stack>
                )}

                {showExample && !showAnswer && wordDetails.example_sentences?.[0] && (
                  <Alert severity="info" sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>Example:</Typography>
                    <Typography paragraph>{wordDetails.example_sentences[0][0]}</Typography>
                    <Typography>{wordDetails.example_sentences[0][1]}</Typography>
                  </Alert>
                )}
              </Box>
            </Stack>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}

export default Practice; 