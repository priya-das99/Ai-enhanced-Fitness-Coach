// Configuration - Load from config.js
const API_BASE_URL = window.API_CONFIG?.API_BASE_URL || 'http://localhost:8000/api/v1';

// DOM Elements
const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');
const showRegisterLink = document.getElementById('showRegister');
const showLoginLink = document.getElementById('showLogin');
const loginError = document.getElementById('loginError');
const registerError = document.getElementById('registerError');

// Switch between login and register forms
showRegisterLink.addEventListener('click', (e) => {
    e.preventDefault();
    loginForm.style.display = 'none';
    registerForm.style.display = 'block';
    loginError.classList.remove('show');
});

showLoginLink.addEventListener('click', (e) => {
    e.preventDefault();
    registerForm.style.display = 'none';
    loginForm.style.display = 'block';
    registerError.classList.remove('show');
});

// Handle Login
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    const submitBtn = loginForm.querySelector('button[type="submit"]');
    
    // Disable button
    submitBtn.disabled = true;
    submitBtn.textContent = 'Logging in...';
    loginError.classList.remove('show');
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Store JWT token and user info
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('user', JSON.stringify(data.user));
            
            // IMPORTANT: Redirect to INDEX.HTML not chat.html
            console.log('Login successful, redirecting to index.html');
            window.location.replace('index.html');
        } else {
            // Show error
            loginError.textContent = data.error || 'Login failed';
            loginError.classList.add('show');
        }
    } catch (error) {
        console.error('Login error:', error);
        loginError.textContent = 'Connection error. Please try again.';
        loginError.classList.add('show');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Login';
    }
});

// Handle Register
registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const fullName = document.getElementById('registerFullName').value;
    const username = document.getElementById('registerUsername').value;
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;
    const submitBtn = registerForm.querySelector('button[type="submit"]');
    
    // Disable button
    submitBtn.disabled = true;
    submitBtn.textContent = 'Creating account...';
    registerError.classList.remove('show');
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                full_name: fullName,
                username,
                email,
                password
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Show success and switch to login
            alert('Account created successfully! Please login.');
            registerForm.style.display = 'none';
            loginForm.style.display = 'block';
            
            // Pre-fill username
            document.getElementById('loginUsername').value = username;
        } else {
            // Show error
            registerError.textContent = data.error || 'Registration failed';
            registerError.classList.add('show');
        }
    } catch (error) {
        console.error('Register error:', error);
        registerError.textContent = 'Connection error. Please try again.';
        registerError.classList.add('show');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Register';
    }
});

// Check if already logged in
window.addEventListener('DOMContentLoaded', async () => {
    console.log('Checking if user is already logged in...');
    const token = localStorage.getItem('token');
    
    if (!token) {
        console.log('No token found, staying on login page');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/me`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            // Already logged in, redirect to INDEX page
            console.log('User already logged in, redirecting to index.html');
            window.location.replace('index.html');
        } else {
            // Token invalid, clear it
            console.log('Token invalid, clearing and staying on login page');
            localStorage.removeItem('token');
            localStorage.removeItem('user');
        }
    } catch (error) {
        // Not logged in, stay on login page
        console.log('Auth check error:', error);
        localStorage.removeItem('token');
        localStorage.removeItem('user');
    }
});
