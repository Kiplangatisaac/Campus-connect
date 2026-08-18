import axios from 'axios';

const sanitizeInput = (str) => {
  if (typeof str !== 'string') return str;
  return str.replace(/[<>]/g, '').replace(/javascript:/gi, '').replace(/on\w+=/gi, '');
};

const sanitizeObject = (obj) => {
  if (!obj || typeof obj !== 'object') return obj;
  if (obj instanceof FormData) return obj;
  const sanitized = {};
  for (const [key, value] of Object.entries(obj)) {
    sanitized[key] = typeof value === 'string' ? sanitizeInput(value) : value;
  }
  return sanitized;
};

const getApiBaseURL = () => {
  if (process.env.REACT_APP_API_URL) return process.env.REACT_APP_API_URL;
  return '/api';
};

const api = axios.create({
  baseURL: getApiBaseURL(),
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type'];
    } else if (config.data && typeof config.data === 'object') {
      config.data = sanitizeObject(config.data);
    }
    return config;
  },
  (error) => Promise.reject(error)
);

let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) prom.reject(error);
    else prom.resolve(token);
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then(token => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return api(originalRequest);
        });
      }
      originalRequest._retry = true;
      isRefreshing = true;
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const { data } = await axios.post(`${api.defaults.baseURL}/auth/refresh`, { refresh_token: refreshToken });
          localStorage.setItem('token', data.access_token);
          localStorage.setItem('refresh_token', data.refresh_token);
          api.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`;
          processQueue(null, data.access_token);
          originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
          return api(originalRequest);
        } catch (refreshError) {
          processQueue(refreshError, null);
          localStorage.removeItem('token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
          return Promise.reject(refreshError);
        } finally {
          isRefreshing = false;
        }
      }
      localStorage.removeItem('token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;

export const socialAuth = {
  getGoogleAuthUrl: async () => {
    const { data } = await api.get('/auth/google/url');
    return data.url;
  },

  getMicrosoftAuthUrl: async () => {
    const { data } = await api.get('/auth/microsoft/url');
    return data.url;
  },

  getAppleAuthUrl: async () => {
    const { data } = await api.get('/auth/apple/url');
    return data.url;
  },

  handleSocialCallback: async (provider, code, state) => {
    const { data } = await api.post(`/auth/${provider}/callback`, { code, state, provider });
    return data;
  },

  linkSocialAccount: async (provider) => {
    const { data } = await api.post(`/auth/${provider}/link`);
    return data;
  },

  unlinkSocialAccount: async (provider) => {
    const { data } = await api.delete(`/auth/${provider}/unlink`);
    return data;
  }
};
