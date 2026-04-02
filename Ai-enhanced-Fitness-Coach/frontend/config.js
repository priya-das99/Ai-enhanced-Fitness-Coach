// API Configuration
// Update PRODUCTION_API_URL with your deployed Render URL
const CONFIG = {
    PRODUCTION_API_URL: 'https://ai-enhanced-fitness-coach.onrender.com/api/v1',
    LOCAL_API_URL: 'http://localhost:8000/api/v1'  // Back to original port 8000
};

// Dynamic API URL based on environment
const getApiBaseUrl = () => {
    return window.location.hostname === 'localhost' 
        ? CONFIG.LOCAL_API_URL
        : CONFIG.PRODUCTION_API_URL;
};

// Export for use in other files
window.API_CONFIG = {
    getApiBaseUrl,
    CONFIG
};