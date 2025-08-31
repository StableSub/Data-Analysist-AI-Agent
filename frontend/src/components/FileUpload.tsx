import React, { useCallback, useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Alert,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Paper
} from '@mui/material';
import { CloudUpload, Description } from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import { FileInfo } from '../types';

interface FileUploadProps {
  onFileUploaded: (fileInfo: FileInfo) => void;
}

const API_BASE_URL = 'http://localhost:8000';

const FileUpload: React.FC<FileUploadProps> = ({ onFileUploaded }) => {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sampleRows, setSampleRows] = useState(100);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    setUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('sample_rows', sampleRows.toString());

      const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const data = response.data;

      if (data.success) {
        const fileInfo: FileInfo = {
          dataset_id: data.dataset_id!,
          meta: data.meta!,
          preview_df: data.preview_df!,
          dtype_df: data.dtype_df!,
        };
        onFileUploaded(fileInfo);
      } else {
        setError(data.message);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || '파일 업로드 중 오류가 발생했습니다.');
    } finally {
      setUploading(false);
    }
  }, [sampleRows, onFileUploaded]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'text/tab-separated-values': ['.tsv'],
      'text/plain': ['.txt'],
    },
    multiple: false,
  });

  return (
    <Box>
      <FormControl fullWidth sx={{ mb: 2 }}>
        <InputLabel>샘플 로딩 행 수</InputLabel>
        <Select
          value={sampleRows}
          label="샘플 로딩 행 수"
          onChange={(e) => setSampleRows(e.target.value as number)}
        >
          <MenuItem value={50}>50행</MenuItem>
          <MenuItem value={100}>100행</MenuItem>
          <MenuItem value={500}>500행</MenuItem>
          <MenuItem value={1000}>1,000행</MenuItem>
          <MenuItem value={2000}>2,000행</MenuItem>
        </Select>
      </FormControl>

      <Paper
        {...getRootProps()}
        sx={{
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : 'grey.300',
          borderRadius: 2,
          p: 4,
          textAlign: 'center',
          cursor: 'pointer',
          backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            borderColor: 'primary.main',
            backgroundColor: 'action.hover',
          },
        }}
      >
        <input {...getInputProps()} />
        {uploading ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
            <CircularProgress size={40} />
            <Typography variant="body1">파일 처리 중...</Typography>
          </Box>
        ) : (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
            <CloudUpload sx={{ fontSize: 48, color: 'primary.main' }} />
            <Typography variant="h6" color="primary">
              {isDragActive ? '파일을 여기에 놓으세요' : '파일을 드래그하거나 클릭하여 업로드'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              CSV, TSV, TXT 파일만 지원됩니다
            </Typography>
            <Button
              variant="outlined"
              startIcon={<Description />}
              sx={{ mt: 1 }}
            >
              파일 선택
            </Button>
          </Box>
        )}
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}
    </Box>
  );
};

export default FileUpload;
