import {
  Box,
  Card,
  CardContent,
  CircularProgress,
  Grid,
  Typography,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { practiceApi } from '../services/api';
import { PracticeStats } from '../types';

function Stats() {
  const { data: stats, isLoading } = useQuery<PracticeStats>({
    queryKey: ['practice-stats'],
    queryFn: async () => {
      const response = await practiceApi.getStats();
      return response.data;
    },
  });

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!stats) {
    return (
      <Typography color="error">
        Failed to load statistics. Please try again later.
      </Typography>
    );
  }

  const statCards = [
    {
      title: 'Total Words',
      value: stats.total_words,
    },
    {
      title: 'Words Started',
      value: stats.words_started,
    },
    {
      title: 'Words Mastered',
      value: stats.words_mastered,
    },
    {
      title: 'Success Rate',
      value: `${(stats.success_rate * 100).toFixed(1)}%`,
    },
    {
      title: 'Total Attempts',
      value: stats.total_attempts,
    },
    {
      title: 'Total Successes',
      value: stats.total_successes,
    },
  ];

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3 }}>
        Practice Statistics
      </Typography>

      <Grid container spacing={3}>
        {statCards.map((stat) => (
          <Grid item xs={12} sm={6} md={4} key={stat.title}>
            <Card>
              <CardContent>
                <Typography variant="h6" color="text.secondary" gutterBottom>
                  {stat.title}
                </Typography>
                <Typography variant="h4">{stat.value}</Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}

export default Stats; 