import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { theme } from './config/theme';
import { AuthProvider } from './contexts/auth';
import Layout from './components/Layout';
import Login from './pages/Login';
import Vocabulary from './pages/Vocabulary';
import Practice from './pages/Practice';
import Stats from './pages/Stats';
import PrivateRoute from './components/PrivateRoute';

const queryClient = new QueryClient();

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <Router>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route element={<PrivateRoute><Layout /></PrivateRoute>}>
                <Route path="/" element={<Navigate to="/vocabulary" replace />} />
                <Route path="/vocabulary" element={<Vocabulary />} />
                <Route path="/practice" element={<Practice />} />
                <Route path="/stats" element={<Stats />} />
              </Route>
            </Routes>
          </Router>
        </AuthProvider>
      </QueryClientProvider>
    </ThemeProvider>
  );
}

export default App;
