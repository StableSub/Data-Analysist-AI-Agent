import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  Typography,
  Alert,
  Paper,
  Divider,
  List,
  ListItem,
  ListItemText,
  Chip,
} from '@mui/material';
import { Person, Save } from '@mui/icons-material';
import axios from 'axios';

interface ProfileSettingsProps {
  open: boolean;
  onClose: () => void;
  onProfileUpdate: () => void;
}

const API_BASE_URL = 'http://localhost:8000';

const ProfileSettings: React.FC<ProfileSettingsProps> = ({ 
  open, 
  onClose, 
  onProfileUpdate 
}) => {
  const [name, setName] = useState('');
  const [allInfo, setAllInfo] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);

  // 프로필 로드
  const loadProfile = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/profile`);
      if (response.data.success && response.data.profile?.personal?.info_list) {
        const infoList = response.data.profile.personal.info_list;
        setAllInfo(infoList);
      } else {
        setAllInfo([]);
      }
      setName(''); // 입력 필드는 항상 비우기
    } catch (err) {
      console.error('프로필 로드 실패:', err);
      setAllInfo([]);
    }
  };

  useEffect(() => {
    if (open) {
      loadProfile();
    }
  }, [open]);

  const handleSave = async () => {
    if (!name.trim()) return;
    
    try {
      setLoading(true);
      
      await axios.post(`${API_BASE_URL}/profile`, {
        category: 'personal',
        key: 'name',
        value: name,
      });
      
      setSuccess('정보가 추가되었습니다!');
      setAllInfo(prev => [...prev, name]); // 새 정보 추가
      setName(''); // 입력 필드 비우기
      setTimeout(() => setSuccess(null), 2000);
      onProfileUpdate();
      
    } catch (err) {
      console.error('저장 실패:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center" gap={1}>
          <Person color="primary" />
          <Typography variant="h6">프로필 설정</Typography>
        </Box>
      </DialogTitle>
      
      <DialogContent>
        {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}
        
        {/* 저장된 모든 정보 표시 */}
        <Paper 
          sx={{ 
            p: 2, 
            mb: 3, 
            backgroundColor: 'grey.50',
            border: '1px solid',
            borderColor: 'grey.300',
            maxHeight: '200px',
            overflow: 'auto'
          }}
        >
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            저장된 정보 ({allInfo.length}개):
          </Typography>
          
          {allInfo.length === 0 ? (
            <Typography 
              variant="body2" 
              sx={{ 
                fontStyle: 'italic',
                color: 'text.secondary',
                textAlign: 'center',
                py: 2
              }}
            >
              저장된 정보가 없습니다.
            </Typography>
          ) : (
            <Box display="flex" flexDirection="column" gap={1}>
              {allInfo.map((info, index) => (
                <Chip
                  key={index}
                  label={`${index + 1}. ${info}`}
                  variant="outlined"
                  size="small"
                  sx={{ 
                    justifyContent: 'flex-start',
                    height: 'auto',
                    py: 1,
                    '& .MuiChip-label': {
                      whiteSpace: 'normal',
                      textAlign: 'left'
                    }
                  }}
                />
              ))}
            </Box>
          )}
        </Paper>

        <Divider sx={{ mb: 3 }} />
        
        <TextField
          fullWidth
          label="정보"
          value={name}
          onChange={(e) => setName(e.target.value)}
          variant="outlined"
          placeholder="AI가 기억할 정보를 입력하세요"
          multiline
          rows={3}
        />
      </DialogContent>
      
      <DialogActions sx={{ p: 3 }}>
        <Button onClick={onClose}>취소</Button>
        <Button
          variant="contained"
          startIcon={<Save />}
          onClick={handleSave}
          disabled={loading || !name.trim()}
        >
          {loading ? '저장 중...' : '저장'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ProfileSettings;