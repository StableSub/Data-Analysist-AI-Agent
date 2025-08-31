import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Card,
  CardContent,
  LinearProgress
} from '@mui/material';
import { ExpandMore, TableChart, Info, DataUsage } from '@mui/icons-material';
import { FileInfo } from '../types';

interface DataPreviewProps {
  fileInfo: FileInfo;
}

const DataPreview: React.FC<DataPreviewProps> = ({ fileInfo }) => {
  const [expanded, setExpanded] = useState<string | false>('panel1');

  const handleAccordionChange = (panel: string) => (event: React.SyntheticEvent, isExpanded: boolean) => {
    setExpanded(isExpanded ? panel : false);
  };

  const getDataTypeColor = (dtype: string) => {
    if (dtype.includes('int') || dtype.includes('float')) return 'primary';
    if (dtype.includes('object')) return 'secondary';
    if (dtype.includes('datetime')) return 'success';
    return 'default';
  };

  return (
    <Box>
      {/* 파일 정보 요약 */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' }, gap: 2, mb: 2 }}>
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 2 }}>
            <Typography variant="h6" color="primary">
              {fileInfo.meta.shape_total[0].toLocaleString()}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              총 행 수
            </Typography>
          </CardContent>
        </Card>
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 2 }}>
            <Typography variant="h6" color="primary">
              {fileInfo.meta.shape_total[1]}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              총 열 수
            </Typography>
          </CardContent>
        </Card>
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 2 }}>
            <Typography variant="h6" color="primary">
              {fileInfo.meta.sniff.filetype.toUpperCase()}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              파일 형식
            </Typography>
          </CardContent>
        </Card>
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 2 }}>
            <Typography variant="h6" color="primary">
              {fileInfo.meta.sniff.encoding.toUpperCase()}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              인코딩
            </Typography>
          </CardContent>
        </Card>
      </Box>

      {/* 데이터 미리보기 */}
      <Accordion expanded={expanded === 'panel1'} onChange={handleAccordionChange('panel1')}>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <TableChart sx={{ mr: 1 }} />
          <Typography variant="h6">데이터 미리보기 (상위 20행)</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <TableContainer component={Paper} sx={{ maxHeight: 400 }}>
            <Table stickyHeader size="small">
              <TableHead>
                <TableRow>
                  {fileInfo.meta.columns.map((column, index) => (
                    <TableCell key={index} sx={{ fontWeight: 'bold', backgroundColor: 'grey.100' }}>
                      {column}
                    </TableCell>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {fileInfo.preview_df.slice(0, 20).map((row, rowIndex) => (
                  <TableRow key={rowIndex} hover>
                    {fileInfo.meta.columns.map((column, colIndex) => (
                      <TableCell key={colIndex} sx={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {String(row[column] || '').substring(0, 50)}
                        {String(row[column] || '').length > 50 && '...'}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </AccordionDetails>
      </Accordion>

      {/* 컬럼 정보 */}
      <Accordion expanded={expanded === 'panel2'} onChange={handleAccordionChange('panel2')}>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Info sx={{ mr: 1 }} />
          <Typography variant="h6">컬럼 정보</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <TableContainer component={Paper}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 'bold' }}>컬럼명</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>데이터 타입</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Null 개수</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Null 비율</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {fileInfo.dtype_df.map((row, index) => (
                  <TableRow key={index} hover>
                    <TableCell sx={{ fontWeight: 'medium' }}>{row.column}</TableCell>
                    <TableCell>
                      <Chip 
                        label={row.dtype} 
                        size="small" 
                        color={getDataTypeColor(row.dtype) as any}
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>{row.null_count.toLocaleString()}</TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Box sx={{ width: '100%', mr: 1 }}>
                          <LinearProgress 
                            variant="determinate" 
                            value={row.null_ratio} 
                            sx={{ height: 8, borderRadius: 4 }}
                          />
                        </Box>
                        <Typography variant="body2" sx={{ minWidth: 35 }}>
                          {row.null_ratio.toFixed(1)}%
                        </Typography>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </AccordionDetails>
      </Accordion>

      {/* 파일 상세 정보 */}
      <Accordion expanded={expanded === 'panel3'} onChange={handleAccordionChange('panel3')}>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <DataUsage sx={{ mr: 1 }} />
          <Typography variant="h6">파일 상세 정보</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2" color="text.secondary">데이터셋 ID:</Typography>
              <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                {fileInfo.dataset_id}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2" color="text.secondary">구분자:</Typography>
              <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                "{fileInfo.meta.sniff.delimiter}"
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2" color="text.secondary">확장자:</Typography>
              <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                .{fileInfo.meta.ext}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2" color="text.secondary">저장 경로:</Typography>
              <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                {fileInfo.meta.raw_path}
              </Typography>
            </Box>
          </Box>
        </AccordionDetails>
      </Accordion>
    </Box>
  );
};

export default DataPreview;
