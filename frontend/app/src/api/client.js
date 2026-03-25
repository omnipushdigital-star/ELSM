import axios from 'axios';

// FastAPI backend base URL
// In dev: http://localhost:8000
// In prod: set VITE_API_URL in .env
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 10000,
});

// Attach JWT token to every request if present
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('elsm_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// On 401, clear session and reload to login
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('elsm_user');
      localStorage.removeItem('elsm_token');
      window.location.reload();
    }
    return Promise.reject(err);
  }
);

export default api;
