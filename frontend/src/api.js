import axios from 'axios';

const api = axios.create({
  baseURL: window.location.origin === 'http://localhost' ? '' : 'http://localhost:8000',
});

export const analyseJob = (data) => api.post('/api/analyse', data);
export const getApplications = () => api.get('/api/applications');
export const getApplicationById = (id) => api.get(`/api/applications/${id}`);

export const reEvaluateJob = (applicationId, feedback) => {
  return api.post('/api/re-evaluate', {
    application_id: applicationId,
    feedback: feedback
  });
};

export const getCVs = () => api.get('/api/cvs');

export const uploadCV = (file, label) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('label', label);
  return api.post('/api/cvs/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
};

export const deleteCV = (id) => api.delete(`/api/cvs/${id}`);
export default api;