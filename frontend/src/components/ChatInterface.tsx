import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  TextField,
  Typography,
  Paper,
  Avatar,
  CircularProgress,
  Alert,
  IconButton
} from '@mui/material';
import { Send, SmartToy, Person } from '@mui/icons-material';
import axios from 'axios';
import { ChatMessage, FileInfo } from '../types';

interface ChatInterfaceProps {
  fileInfo: FileInfo | null;
}

const API_BASE_URL = 'http://localhost:8000';

const ChatInterface: React.FC<ChatInterfaceProps> = ({ fileInfo }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // 초기 메시지 로드
    loadMessages();
  }, []);

  const loadMessages = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/messages`);
      setMessages(response.data.messages);
    } catch (err) {
      console.error('메시지 로드 실패:', err);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: inputMessage,
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    setError(null);

    try {
      const response = await axios.post(`${API_BASE_URL}/chat`, {
        message: inputMessage,
      });

      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.data.response,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err: any) {
      setError(err.response?.data?.detail || '메시지 전송 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  const formatMessage = (content: string) => {
    // 코드 블록과 일반 텍스트를 구분하여 렌더링
    const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
    const parts = content.split(codeBlockRegex);
    
    return parts.map((part, index) => {
      if (index % 3 === 1) {
        // 언어 지정자 (예: python, javascript)
        return null;
      } else if (index % 3 === 2) {
        // 코드 블록 내용
        return (
          <Paper
            key={index}
            sx={{
              p: 2,
              my: 1,
              backgroundColor: 'grey.100',
              fontFamily: 'monospace',
              fontSize: '0.875rem',
              overflow: 'auto',
              maxHeight: '300px',
            }}
          >
            <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{part}</pre>
          </Paper>
        );
      } else {
        // 일반 텍스트
        return (
          <Typography key={index} variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
            {part}
          </Typography>
        );
      }
    });
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* 파일 정보 표시 */}
      {fileInfo && (
        <Paper sx={{ p: 2, mb: 2, backgroundColor: 'success.light', color: 'success.contrastText' }}>
          <Typography variant="body2">
            📊 데이터셋 ID: {fileInfo.dataset_id} | 
            📈 {fileInfo.meta.shape_total[0].toLocaleString()}행 × {fileInfo.meta.shape_total[1]}열 |
            📁 {fileInfo.meta.sniff.filetype.toUpperCase()}
          </Typography>
        </Paper>
      )}

      {/* 메시지 영역 */}
      <Box sx={{ flex: 1, overflow: 'auto', mb: 2 }}>
        {messages.map((message, index) => (
          <Box
            key={index}
            sx={{
              display: 'flex',
              mb: 2,
              justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start',
            }}
          >
            <Box
              sx={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: 1,
                maxWidth: '80%',
              }}
            >
              {message.role === 'assistant' && (
                <Avatar sx={{ bgcolor: 'primary.main', width: 32, height: 32 }}>
                  <SmartToy />
                </Avatar>
              )}
              <Paper
                sx={{
                  p: 2,
                  backgroundColor: message.role === 'user' ? 'primary.main' : 'background.paper',
                  color: message.role === 'user' ? 'primary.contrastText' : 'text.primary',
                  borderRadius: 2,
                  maxWidth: '100%',
                }}
              >
                {formatMessage(message.content)}
              </Paper>
              {message.role === 'user' && (
                <Avatar sx={{ bgcolor: 'secondary.main', width: 32, height: 32 }}>
                  <Person />
                </Avatar>
              )}
            </Box>
          </Box>
        ))}
        
        {isLoading && (
          <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
              <Avatar sx={{ bgcolor: 'primary.main', width: 32, height: 32 }}>
                <SmartToy />
              </Avatar>
              <Paper sx={{ p: 2, borderRadius: 2 }}>
                <CircularProgress size={20} />
              </Paper>
            </Box>
          </Box>
        )}
        
        <div ref={messagesEndRef} />
      </Box>

      {/* 에러 메시지 */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* 입력 영역 */}
      <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
        <TextField
          fullWidth
          multiline
          maxRows={4}
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="데이터에 대해 질문해보세요..."
          disabled={isLoading}
          sx={{
            '& .MuiOutlinedInput-root': {
              borderRadius: 2,
            },
          }}
        />
        <IconButton
          onClick={sendMessage}
          disabled={!inputMessage.trim() || isLoading}
          color="primary"
          sx={{
            bgcolor: 'primary.main',
            color: 'white',
            '&:hover': {
              bgcolor: 'primary.dark',
            },
            '&:disabled': {
              bgcolor: 'grey.300',
              color: 'grey.500',
            },
          }}
        >
          <Send />
        </IconButton>
      </Box>
    </Box>
  );
};

export default ChatInterface;
