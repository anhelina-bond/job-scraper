import axios from 'axios';

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000',
});

export const analyseJob = (data) => api.post('/api/analyse', data);
export const getApplications = () => api.get('/api/applications');

export const reEvaluateJob = (applicationId, feedback) => {
  return api.post('/api/re-evaluate', {
    application_id: applicationId,
    feedback: feedback
  });
};
export default api;