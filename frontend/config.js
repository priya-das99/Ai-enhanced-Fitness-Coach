// API Configuration
// Update PRODUCTION_API_URL with your deployed Render URL
const CONFIG = {
    PRODUCTION_API_URL: 'https://ai-enhanced-fitness-coach.onrender.com/api/v1',
    LOCAL_API_URL: 'http://localhost:8000/api/v1'
};

// Dynamic API URL based on environment
const API_BASE_URL = window.location.hostname === 'localhost' 
    ? CONFIG.LOCAL_API_URL
    : CONFIG.PRODUCTION_API_URL;

// Export for use in other files
window.API_CONFIG = {
    API_BASE_URL,
    CONFIG
};