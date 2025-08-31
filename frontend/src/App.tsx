import React, { useState } from 'react';
import {
  Box,
  CssBaseline,
  ThemeProvider,
  createTheme,
  Container,
  Paper,
  Typography,
  AppBar,
  Toolbar,
  IconButton,
  useMediaQuery,
  Button
} from '@mui/material';
import { Brightness4, Brightness7, DeleteSweep, Person } from '@mui/icons-material';
import FileUpload from './components/FileUpload';
import ChatInterface from './components/ChatInterface';
import DataPreview from './components/DataPreview';
import ProfileSettings from './components/ProfileSettings';
import { FileInfo } from './types';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
    },
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 12,
        },
      },
    },
  },
});

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#90caf9',
    },
    secondary: {
      main: '#f48fb1',
    },
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
    },
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 12,
        },
      },
    },
  },
});

function App() {
  const [currentTheme, setCurrentTheme] = useState(theme);
  const [fileInfo, setFileInfo] = useState<FileInfo | null>(null);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const isMobile = useMediaQuery('(max-width:768px)');

  const toggleTheme = () => {
    setIsDarkMode(!isDarkMode);
    setCurrentTheme(isDarkMode ? theme : darkTheme);
  };

  const clearAllData = async () => {
    try {
      const response = await fetch('http://localhost:8000/clear-data', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        setFileInfo(null); // 프론트엔드 상태도 초기화
        alert('모든 데이터가 성공적으로 삭제되었습니다.');
        window.location.reload(); // 페이지 새로고침으로 완전 초기화
      } else {
        alert('데이터 삭제에 실패했습니다.');
      }
    } catch (error) {
      console.error('데이터 삭제 오류:', error);
      alert('데이터 삭제 중 오류가 발생했습니다.');
    }
  };

  return (
    <ThemeProvider theme={currentTheme}>
      <CssBaseline />
      <Box sx={{ flexGrow: 1, minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        <AppBar position="static" elevation={0}>
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              📊 Data Analysis AI Agent
            </Typography>
            <Button
              color="inherit"
              startIcon={<Person />}
              onClick={() => setProfileOpen(true)}
              sx={{ mr: 1 }}
            >
              프로필 설정
            </Button>
            <Button
              color="inherit"
              startIcon={<DeleteSweep />}
              onClick={clearAllData}
              sx={{ mr: 1 }}
            >
              데이터 초기화
            </Button>
            <IconButton color="inherit" onClick={toggleTheme}>
              {isDarkMode ? <Brightness7 /> : <Brightness4 />}
            </IconButton>
          </Toolbar>
        </AppBar>

        <Container maxWidth="xl" sx={{ flexGrow: 1, py: 3 }}>
          <Box sx={{ display: 'flex', flexDirection: isMobile ? 'column' : 'row', gap: 3, height: 'calc(100vh - 140px)' }}>
            {/* 왼쪽 패널 - 파일 업로드 및 데이터 미리보기 */}
            <Box sx={{ 
              width: isMobile ? '100%' : '40%', 
              display: 'flex', 
              flexDirection: 'column', 
              gap: 2 
            }}>
              <Paper elevation={2} sx={{ p: 3, flex: '0 0 auto' }}>
                <Typography variant="h5" gutterBottom sx={{ mb: 2 }}>
                  📁 파일 업로드
                </Typography>
                <FileUpload onFileUploaded={setFileInfo} />
              </Paper>

              {fileInfo && (
                <Paper elevation={2} sx={{ p: 3, flex: 1, overflow: 'auto' }}>
                  <DataPreview fileInfo={fileInfo} />
                </Paper>
              )}
            </Box>

            {/* 오른쪽 패널 - 채팅 인터페이스 */}
            <Box sx={{ 
              width: isMobile ? '100%' : '60%', 
              display: 'flex', 
              flexDirection: 'column' 
            }}>
              <Paper elevation={2} sx={{ p: 3, flex: 1, display: 'flex', flexDirection: 'column' }}>
                <Typography variant="h5" gutterBottom sx={{ mb: 2 }}>
                  💬 AI Assistant
                </Typography>
                <ChatInterface fileInfo={fileInfo} />
              </Paper>
            </Box>
          </Box>
        </Container>

        {/* 프로필 설정 다이얼로그 */}
        <ProfileSettings
          open={profileOpen}
          onClose={() => setProfileOpen(false)}
          onProfileUpdate={() => {
            // 프로필 업데이트 시 필요한 로직 (예: 채팅 새로고침 등)
            console.log('Profile updated');
          }}
        />
      </Box>
    </ThemeProvider>
  );
}

export default App;
