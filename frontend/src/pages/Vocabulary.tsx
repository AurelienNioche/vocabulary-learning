import { useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  IconButton,
  TextField,
  Typography,
} from '@mui/material';
import { Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { vocabularyApi } from '../services/api';
import { WordEntry } from '../types';

function Vocabulary() {
  const [open, setOpen] = useState(false);
  const [editWord, setEditWord] = useState<WordEntry | null>(null);
  const queryClient = useQueryClient();

  const { data: words = [], isLoading } = useQuery<string[]>({
    queryKey: ['vocabulary'],
    queryFn: async () => {
      const response = await vocabularyApi.getAll();
      return response.data;
    },
  });

  const addMutation = useMutation({
    mutationFn: vocabularyApi.addWord,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vocabulary'] });
      setOpen(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ word, wordEntry }: { word: string; wordEntry: WordEntry }) =>
      vocabularyApi.updateWord(word, wordEntry),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vocabulary'] });
      setOpen(false);
      setEditWord(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: vocabularyApi.deleteWord,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vocabulary'] });
    },
  });

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const wordEntry: WordEntry = {
      word: formData.get('word') as string,
      translations: (formData.get('translations') as string).split('/'),
      example_sentences: formData.get('example') 
        ? [[formData.get('example') as string, formData.get('translation') as string]]
        : [],
    };

    if (editWord) {
      updateMutation.mutate({ word: editWord.word, wordEntry });
    } else {
      addMutation.mutate(wordEntry);
    }
  };

  const handleEdit = async (word: string) => {
    const response = await vocabularyApi.getWord(word);
    setEditWord(response.data);
    setOpen(true);
  };

  if (isLoading) {
    return <Typography>Loading...</Typography>;
  }

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4">Vocabulary</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => {
            setEditWord(null);
            setOpen(true);
          }}
        >
          Add Word
        </Button>
      </Box>

      <Grid container spacing={2}>
        {words.map((word: string) => (
          <Grid item xs={12} sm={6} md={4} key={word}>
            <Card>
              <CardContent>
                <Typography variant="h6">{word}</Typography>
                <Box sx={{ mt: 1, display: 'flex', justifyContent: 'flex-end' }}>
                  <IconButton onClick={() => handleEdit(word)}>
                    <EditIcon />
                  </IconButton>
                  <IconButton onClick={() => deleteMutation.mutate(word)} color="error">
                    <DeleteIcon />
                  </IconButton>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editWord ? 'Edit Word' : 'Add New Word'}</DialogTitle>
        <form onSubmit={handleSubmit}>
          <DialogContent>
            <TextField
              autoFocus
              margin="dense"
              name="word"
              label="Japanese Word"
              fullWidth
              defaultValue={editWord?.word || ''}
            />
            <TextField
              margin="dense"
              name="translations"
              label="French Translations (separate with /)"
              fullWidth
              defaultValue={editWord?.translations.join('/') || ''}
            />
            <TextField
              margin="dense"
              name="example"
              label="Example Sentence (Japanese)"
              fullWidth
              defaultValue={editWord?.example_sentences?.[0]?.[0] || ''}
            />
            <TextField
              margin="dense"
              name="translation"
              label="Example Translation (French)"
              fullWidth
              defaultValue={editWord?.example_sentences?.[0]?.[1] || ''}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpen(false)}>Cancel</Button>
            <Button type="submit" variant="contained">
              {editWord ? 'Update' : 'Add'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </Box>
  );
}

export default Vocabulary; 