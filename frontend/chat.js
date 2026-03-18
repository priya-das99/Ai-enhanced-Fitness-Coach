// Configuration - Load from config.js
const API_BASE_URL = window.API_CONFIG?.getApiBaseUrl() || 'http://localhost:8000/api/v1';
let currentUser = null;

// Helper function to get auth headers
function getAuthHeaders() {
    const token = localStorage.getItem('token');
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };
}

// DOM Elements
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const emojiSelector = document.getElementById('emojiSelector');
const textInputContainer = document.getElementById('textInputContainer');
const skipContainer = document.getElementById('skipContainer');
const skipButton = document.getElementById('skipButton');
const chatbotButton = document.getElementById('chatbotButton');
const chatContainer = document.querySelector('.chat-container');
const chatbotBadge = document.getElementById('chatbotBadge');

// State
let isWaitingForResponse = false;
let isChatOpen = false;
let hasNewMessage = false;
let lastActivityButtonsLocation = null;

// Check authentication on page load
document.addEventListener('DOMContentLoaded', async () => {
    await checkAuth();
    updateNavigation();
    if (currentUser) {
        initializeChat();
        setupEventListeners();
        setupDemoReminderButtons(); // Add demo reminder buttons
        
        // Start notification polling after user is authenticated
        if (typeof startNotificationPolling === 'function') {
            console.log('🔔 Starting notification polling for user:', currentUser.username);
            startNotificationPolling();
        } else {
            console.log('⚠️ Notification polling function not found - system_notifications.js may not be loaded');
        }
        
        // Check if returning from module
        if (typeof checkModuleCompletion === 'function') {
            setTimeout(() => checkModuleCompletion(), 500);
        }
        
        // Check if returning from external activity (NEW!)
        setTimeout(() => checkPendingActivity(), 600);
    } else {
        setupEventListeners(); // Still setup listeners for login button
    }
});

// Listen for tab visibility changes to detect when user returns
document.addEventListener('visibilitychange', () => {
    if (!document.hidden && currentUser) {
        // User returned to this tab - check for pending activities
        console.log('Tab became visible - checking for pending activities');
        setTimeout(() => checkPendingActivity(), 300);
    }
});

// Update navigation based on auth status
function updateNavigation() {
    const loginBtn = document.getElementById('loginBtn');
    const navLogoutBtn = document.getElementById('navLogoutBtn');
    const userGreeting = document.getElementById('userGreeting');
    const heroButtons = document.querySelector('.hero-buttons');
    
    if (currentUser) {
        // User is logged in
        if (loginBtn) loginBtn.style.display = 'none';
        if (navLogoutBtn) {
            navLogoutBtn.style.display = 'inline-block';
            navLogoutBtn.addEventListener('click', logout);
        }
        if (userGreeting) {
            userGreeting.textContent = `Hi, ${currentUser.full_name || currentUser.username}!`;
            userGreeting.style.display = 'inline-block';
        }
        
        // Update hero buttons to show dashboard instead of login
        if (heroButtons) {
            heroButtons.innerHTML = `
                <button class="btn-primary" onclick="document.getElementById('chatbotButton').click()">Open Chat</button>
                <a href="#features" class="btn-secondary">Learn More</a>
            `;
        }
    } else {
        // User is not logged in
        if (loginBtn) loginBtn.style.display = 'inline-block';
        if (navLogoutBtn) navLogoutBtn.style.display = 'none';
        if (userGreeting) userGreeting.style.display = 'none';
    }
}

// Check if user is authenticated
async function checkAuth() {
    const token = localStorage.getItem('token');
    
    if (!token) {
        currentUser = null;
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/me`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            currentUser = data;
            
            // Update chat header with user info
            const subtitle = document.querySelector('.subtitle');
            if (subtitle) {
                subtitle.textContent = `Welcome, ${currentUser.full_name || currentUser.username}!`;
            }
        } else {
            // Token invalid or expired
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            currentUser = null;
        }
    } catch (error) {
        console.error('Auth check failed:', error);
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        currentUser = null;
    }
}

// Setup event listeners
function setupEventListeners() {
    // Always setup send button listener (with auth check)
    sendButton.addEventListener('click', () => {
        if (!currentUser) {
            alert('Please login to use the chat assistant.');
            window.location.href = 'login.html';
            return;
        }
        sendMessage();
    });
    
    // Only setup other chat listeners if user is authenticated
    if (currentUser) {
        skipButton.addEventListener('click', () => sendMessage('skip'));
        
        // Chatbot button toggle
        chatbotButton.addEventListener('click', toggleChat);
        
        // Minimize button
        const minimizeBtn = document.getElementById('minimizeBtn');
        if (minimizeBtn) {
            minimizeBtn.addEventListener('click', closeChat);
        }
        
        // Don't auto-close chat when clicking outside - let user control it manually
        // This prevents the chat from closing when interacting with inline buttons
        
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (!currentUser) {
                    alert('Please login to use the chat assistant.');
                    window.location.href = 'login.html';
                    return;
                }
                sendMessage();
            }
        });
        
        // Emoji button listeners
        document.querySelectorAll('.emoji-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const emoji = btn.getAttribute('data-emoji');
                const label = btn.getAttribute('data-label') || btn.textContent.trim();
                sendMessage(emoji, `${emoji} ${label}`);
            });
        });
    } else {
        // User not logged in - show login prompt when clicking chatbot
        if (chatbotButton) {
            chatbotButton.addEventListener('click', () => {
                if (confirm('Please login to use the chat assistant. Would you like to go to the login page?')) {
                    window.location.href = 'login.html';
                }
            });
        }
    }
}

// Setup demo reminder buttons
function setupDemoReminderButtons() {
    const demoContainer = document.getElementById('demoReminderContainer');
    const waterBtn = document.getElementById('sendWaterReminderBtn');
    const challengeBtn = document.getElementById('sendChallengeReminderBtn');
    const bothBtn = document.getElementById('sendBothRemindersBtn');
    const toggleBtn = document.getElementById('toggleDemoBtn');
    
    if (!demoContainer) return;
    
    // Show demo buttons for authenticated users
    if (currentUser) {
        demoContainer.style.display = 'block';
        
        // Water reminder button
        if (waterBtn) {
            waterBtn.addEventListener('click', async () => {
                try {
                    waterBtn.disabled = true;
                    waterBtn.textContent = '💧 Sending...';
                    
                    const response = await fetch(`${API_BASE_URL}/chat/demo/water-reminder`, {
                        method: 'POST',
                        headers: getAuthHeaders()
                    });
                    
                    if (response.ok) {
                        const data = await response.json();
                        console.log('💧 Water reminder response:', data);
                        addMessage('system', `✅ ${data.message}`);
                        
                        // Force immediate notification check for new reminders
                        console.log('🔔 Triggering notification check in 500ms...');
                        setTimeout(() => {
                            if (typeof forceNotificationCheck === 'function') {
                                console.log('🚀 Calling forceNotificationCheck...');
                                forceNotificationCheck();
                            } else if (typeof window.forceNotificationCheck === 'function') {
                                console.log('🚀 Calling window.forceNotificationCheck...');
                                window.forceNotificationCheck();
                            } else {
                                console.error('❌ forceNotificationCheck function not available');
                                console.log('🔄 Falling back to loadChatHistory...');
                                // Fallback: reload chat history to show the notification
                                loadChatHistory();
                            }
                        }, 500);
                        
                        // ADDITIONAL FIX: Also try to display the notification directly
                        setTimeout(() => {
                            console.log('🎯 Direct notification display attempt...');
                            if (typeof window.displaySystemNotification === 'function') {
                                const directNotification = {
                                    id: 'direct-' + Date.now(),
                                    title: '💧 Hydration Reminder',
                                    message: "💡 💧 Hydration Reminder\n\nIt's time to drink some water! Stay hydrated for better health and energy.",
                                    timestamp: new Date().toISOString(),
                                    action_buttons: [
                                        { id: 'log_water', label: '💧 Log Water' },
                                        { id: 'snooze_reminder', label: '⏰ Remind Later' }
                                    ]
                                };
                                window.displaySystemNotification(directNotification);
                                console.log('✅ Direct notification displayed');
                            }
                        }, 1000);
                    } else {
                        console.error('❌ Water reminder failed:', response.status);
                        addMessage('system', '❌ Failed to send water reminder');
                    }
                } catch (error) {
                    console.error('Error sending water reminder:', error);
                    addMessage('system', '❌ Error sending water reminder');
                } finally {
                    waterBtn.disabled = false;
                    waterBtn.textContent = '💧 Water Reminder';
                }
            });
        }
        
        // Challenge reminder button
        if (challengeBtn) {
            challengeBtn.addEventListener('click', async () => {
                try {
                    challengeBtn.disabled = true;
                    challengeBtn.textContent = '🎯 Sending...';
                    
                    const response = await fetch(`${API_BASE_URL}/chat/demo/challenge-reminder`, {
                        method: 'POST',
                        headers: getAuthHeaders()
                    });
                    
                    if (response.ok) {
                        const data = await response.json();
                        console.log('🎯 Challenge reminder response:', data);
                        addMessage('system', `✅ ${data.message}`);
                        
                        // Force immediate notification check for new reminders
                        console.log('🔔 Triggering notification check in 500ms...');
                        setTimeout(() => {
                            if (typeof forceNotificationCheck === 'function') {
                                console.log('🚀 Calling forceNotificationCheck...');
                                forceNotificationCheck();
                            } else if (typeof window.forceNotificationCheck === 'function') {
                                console.log('🚀 Calling window.forceNotificationCheck...');
                                window.forceNotificationCheck();
                            } else {
                                console.error('❌ forceNotificationCheck function not available');
                                console.log('🔄 Falling back to loadChatHistory...');
                                // Fallback: reload chat history to show the notification
                                loadChatHistory();
                            }
                        }, 500);
                        
                        // ADDITIONAL FIX: Also try to display the notification directly
                        setTimeout(() => {
                            console.log('🎯 Direct challenge notification display attempt...');
                            if (typeof window.displaySystemNotification === 'function') {
                                const directNotification = {
                                    id: 'direct-challenge-' + Date.now(),
                                    title: '🎯 Daily Challenge',
                                    message: "💡 🎯 Daily Challenge\n\nReady for today's challenge? Complete a 10-minute mindfulness session to boost your focus and well-being!",
                                    timestamp: new Date().toISOString(),
                                    action_buttons: [
                                        { id: 'start_challenge', label: '🚀 Start Challenge' },
                                        { id: 'view_progress', label: '📊 View Progress' },
                                        { id: 'snooze_challenge', label: '⏰ Remind Later' }
                                    ]
                                };
                                window.displaySystemNotification(directNotification);
                                console.log('✅ Direct challenge notification displayed');
                            }
                        }, 1000);
                    } else {
                        console.error('❌ Challenge reminder failed:', response.status);
                        addMessage('system', '❌ Failed to send challenge reminder');
                    }
                } catch (error) {
                    console.error('Error sending challenge reminder:', error);
                    addMessage('system', '❌ Error sending challenge reminder');
                } finally {
                    challengeBtn.disabled = false;
                    challengeBtn.textContent = '🎯 Challenge Reminder';
                }
            });
        }
        
        // Both reminders button
        if (bothBtn) {
            bothBtn.addEventListener('click', async () => {
                try {
                    bothBtn.disabled = true;
                    bothBtn.textContent = '🚀 Sending...';
                    
                    const response = await fetch(`${API_BASE_URL}/chat/demo/reminders`, {
                        method: 'POST',
                        headers: getAuthHeaders()
                    });
                    
                    if (response.ok) {
                        const data = await response.json();
                        addMessage('system', `✅ ${data.message}`);
                        // Force immediate notification check for new reminders
                        setTimeout(() => {
                            if (typeof forceNotificationCheck === 'function') {
                                forceNotificationCheck();
                            }
                        }, 500); // Reduced delay for faster response
                    } else {
                        addMessage('system', '❌ Failed to send reminders');
                    }
                } catch (error) {
                    console.error('Error sending reminders:', error);
                    addMessage('system', '❌ Error sending reminders');
                } finally {
                    bothBtn.disabled = false;
                    bothBtn.textContent = '🚀 Both Reminders';
                }
            });
        }
        
        // Toggle demo buttons visibility
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => {
                const isHidden = demoContainer.style.display === 'none';
                demoContainer.style.display = isHidden ? 'block' : 'none';
                toggleBtn.textContent = isHidden ? 'Hide Demo' : 'Show Demo';
            });
        }
    } else {
        demoContainer.style.display = 'none';
    }
}

// Toggle chat visibility
function toggleChat() {
    isChatOpen = !isChatOpen;
    if (isChatOpen) {
        openChat();
    } else {
        closeChat();
    }
}

// Open chat
function openChat() {
    isChatOpen = true;
    chatContainer.classList.add('open');
    messageInput.focus();
    
    // Clear notification badge
    hasNewMessage = false;
    chatbotBadge.style.display = 'none';
    
    // Check if Quick Actions button should be shown when chat opens
    setTimeout(() => {
        if (currentUser) {
            showPinButton();
        }
    }, 300); // Small delay to allow chat to fully open
}

// Close chat
function closeChat() {
    isChatOpen = false;
    chatContainer.classList.remove('open');
}

// Show notification badge
function showNotificationBadge() {
    if (!isChatOpen) {
        hasNewMessage = true;
        chatbotBadge.style.display = 'flex';
    }
}

// Logout function
async function logout() {
    try {
        const token = localStorage.getItem('token');
        if (token) {
            await fetch(`${API_BASE_URL}/auth/logout`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
        }
        
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        currentUser = null;
        
        // Reload the page to update UI
        window.location.reload();
    } catch (error) {
        console.error('Logout error:', error);
        // Force clear and reload anyway
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.reload();
    }
}

// Trigger external module
function triggerModule(moduleId, moduleName) {
    console.log(`🚀 Triggering module: ${moduleId} (${moduleName})`);
    
    // Create a custom event that the parent app can listen to
    const moduleEvent = new CustomEvent('triggerModule', {
        detail: {
            moduleId: moduleId,
            moduleName: moduleName,
            timestamp: new Date().toISOString()
        }
    });
    
    // Dispatch the event
    window.dispatchEvent(moduleEvent);
    
    // Also try postMessage for iframe communication
    if (window.parent !== window) {
        window.parent.postMessage({
            type: 'TRIGGER_MODULE',
            moduleId: moduleId,
            moduleName: moduleName
        }, '*');
    }
    
    // Log for debugging
    console.log(`✅ Module trigger event dispatched for: ${moduleId}`);
    
    // Show a visual indicator in the chat
    const moduleIndicator = document.createElement('div');
    moduleIndicator.className = 'message system module-trigger';
    moduleIndicator.innerHTML = `
        <div class="module-trigger-content">
            <span class="module-icon">🚀</span>
            <span class="module-text">Launching ${moduleName}...</span>
        </div>
    `;
    chatMessages.appendChild(moduleIndicator);
    scrollToBottom();
}

// Initialize chat session
async function initializeChat() {
    try {
        // Load chat history first
        await loadChatHistory();
        
        const response = await fetch(`${API_BASE_URL}/chat/init`, {
            headers: getAuthHeaders()
        });
        
        if (response.status === 401) {
            // Token expired, redirect to login
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            window.location.href = 'login.html';
            return;
        }
        
        const data = await response.json();
        
        // Only display initial message if it exists and no chat history was loaded
        if (data.message && (!chatMessages || chatMessages.children.length === 0)) {
            addMessage('assistant', data.message);
        }
        
        // Show UI elements based on response
        updateUIElements(data.ui_elements || [], data);
        
    } catch (error) {
        console.error('Error initializing chat:', error);
        addMessage('assistant', 'Hi! I had trouble connecting. Please refresh the page.');
    }
}

async function loadChatHistory() {
    try {
        const response = await fetch(`${API_BASE_URL}/chat/messages?limit=200`, {
            headers: getAuthHeaders()
        });
        
        if (response.ok) {
            const data = await response.json();
            const messages = data.messages || [];
            
            // Clear existing messages
            if (chatMessages) {
                chatMessages.innerHTML = '';
            }

            let lastDateLabel = null;

            // Add messages in chronological order with date separators
            messages.forEach(msg => {
                // Inject a date separator when the date changes
                const msgDate = new Date(msg.timestamp);
                const dateLabel = formatDateLabel(msgDate);
                if (dateLabel !== lastDateLabel) {
                    const sep = document.createElement('div');
                    sep.className = 'chat-date-separator';
                    sep.innerHTML = `<span>${dateLabel}</span>`;
                    chatMessages.appendChild(sep);
                    lastDateLabel = dateLabel;
                }

                if (msg.sender === 'system') {
                    // Only show recent system messages (last 2 minutes) as notifications
                    const now = new Date();
                    const diffMinutes = (now - msgDate) / (1000 * 60);
                    if (diffMinutes <= 2) {
                        const notification = {
                            id: msg.id,
                            title: extractNotificationTitle ? extractNotificationTitle(msg.message) : 'System Notification',
                            message: msg.message,
                            timestamp: msg.timestamp,
                            action_buttons: generateActionButtons ? generateActionButtons(msg.message) : []
                        };
                        if (typeof displaySystemNotification === 'function') {
                            displaySystemNotification(notification);
                        } else if (typeof window.displaySystemNotification === 'function') {
                            window.displaySystemNotification(notification);
                        } else {
                            addMessage('assistant', msg.message);
                        }
                    }
                } else {
                    const role = msg.sender === 'user' ? 'user' : 'assistant';
                    addMessage(role, msg.message);
                }
            });
            
            // Always land on the latest message
            scrollToBottom();
        }
    } catch (error) {
        console.error('Error loading chat history:', error);
    }
}

function formatDateLabel(date) {
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(today.getDate() - 1);

    const isSameDay = (a, b) =>
        a.getFullYear() === b.getFullYear() &&
        a.getMonth() === b.getMonth() &&
        a.getDate() === b.getDate();

    if (isSameDay(date, today)) return 'Today';
    if (isSameDay(date, yesterday)) return 'Yesterday';
    return date.toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric', year: 'numeric' });
}

// Send message
async function sendMessage(customMessage = null, displayMessage = null) {
    const message = customMessage || messageInput.value.trim();
    const displayText = displayMessage || message;
    
    if (!message || isWaitingForResponse) {
        console.log('Message blocked:', !message ? 'empty message' : 'waiting for response');
        return;
    }
    
    // Ensure sendButton exists
    if (!sendButton) {
        console.error('Send button not found!');
        return;
    }
    
    // Check if this is an internal message that shouldn't be displayed
    const isInternalMessage = message.startsWith('returned_from_') || message.startsWith('start_');
    
    // Add user message to chat (unless it's 'skip' or an internal message)
    if (!isInternalMessage) {
        if (message.toLowerCase() !== 'skip') {
            addMessage('user', displayText);
        } else {
            addMessage('user', 'Skip', 'skip-message');
        }
    }
    
    messageInput.value = '';
    
    // Show typing indicator
    const typingId = showTypingIndicator();
    isWaitingForResponse = true;
    sendButton.disabled = true;
    console.log('Send button disabled, sending message...');
    
    try {
        const response = await fetch(`${API_BASE_URL}/chat/message`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                message: message
            })
        });
        
        if (response.status === 401) {
            // Token expired, redirect to login
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            window.location.href = 'login.html';
            return;
        }
        
        const data = await response.json();
        
        // Remove typing indicator
        removeTypingIndicator(typingId);
        
        // Add assistant response (only if message is not empty)
        if (data.message && data.message.trim()) {
            addMessage('assistant', data.message);
        }
        
        // Only show notification badge if chat is closed (don't auto-open)
        if (!isChatOpen && data.message && data.message.trim()) {
            showNotificationBadge();
        }
        
        // Check if a module should be triggered
        if (data.trigger_module) {
            console.log(`🚀 Module trigger requested: ${data.trigger_module}`);
            triggerModule(data.trigger_module, data.module_name);
        }
        
        // Update UI elements based on response
        updateUIElements(data.ui_elements || [], data);
        
    } catch (error) {
        console.error('Error sending message:', error);
        removeTypingIndicator(typingId);
        addMessage('assistant', 'Sorry, I had trouble processing that. Please try again.');
    } finally {
        // Always re-enable the button
        isWaitingForResponse = false;
        if (sendButton) {
            sendButton.disabled = false;
            console.log('Send button re-enabled');
        }
        if (messageInput) {
            messageInput.focus();
        }
    }
}

// Update UI elements based on backend response
function updateUIElements(elements, data = {}) {
    console.log('updateUIElements called with:', elements, data);
    
    // Hide all dynamic UI elements first
    emojiSelector.style.display = 'none';
    skipContainer.style.display = 'none';
    textInputContainer.style.display = 'flex';
    
    // Remove any existing inline selectors
    // Activity buttons persist UNLESS we're showing emoji_selector or reason_selector
    const shouldRemoveActivityButtons = elements.includes('emoji_selector') || elements.includes('reason_selector');
    
    const selectorToRemove = shouldRemoveActivityButtons 
        ? '.inline-emoji-selector, .inline-reason-selector, .inline-action-buttons, .inline-activity-buttons, .inline-generic-buttons'
        : '.inline-emoji-selector, .inline-reason-selector, .inline-action-buttons';
    
    const existingSelectors = document.querySelectorAll(selectorToRemove);
    existingSelectors.forEach(el => {
        // Don't remove if it contains a selected button (user already made a choice)
        const hasSelectedButton = el.querySelector('.selected');
        if (!hasSelectedButton) {
            el.remove();
        }
    });
    
    // NEW: Check if elements is an array of button objects (not strings)
    const hasButtonObjects = elements.length > 0 && typeof elements[0] === 'object' && elements[0].type === 'button';
    
    if (hasButtonObjects) {
        // Render generic buttons from backend
        showInlineGenericButtons(elements);
        textInputContainer.style.display = 'none';
        return; // Don't process other element types
    }
    
    // Show requested elements
    if (elements.includes('emoji_selector')) {
        showInlineEmojiSelector();
        textInputContainer.style.display = 'none';
    }
    
    if (elements.includes('reason_selector') && data.reasons) {
        showInlineReasonSelector(data.reasons);
        textInputContainer.style.display = 'none';
    }
    
    if (elements.includes('action_buttons') && data.action) {
        showInlineActionButtons(data.action);
        textInputContainer.style.display = 'none';
    }
    
    // NEW: Support for multiple action buttons
    if (elements.includes('action_buttons_multiple') && data.actions) {
        // Check if these are feedback buttons (simple yes/no/skip style)
        const isFeedbackButtons = data.actions.length === 3 && 
            data.actions.some(a => a.id === 'helpful' || a.id === 'not_helpful' || a.id === 'skip_feedback');
        
        if (isFeedbackButtons) {
            showSimpleFeedbackButtons(data.actions);
        } else {
            showInlineMultipleActionButtons(data.actions);
        }
        textInputContainer.style.display = 'none';
    }
    
    // NEW: Support for activity buttons - handle multiple field names
    if (elements.includes('activity_buttons')) {
        // Backend might send activity_options, suggestions, activities, or buttons
        const activities = data.activity_options || data.suggestions || data.activities || data.buttons || [];
        if (activities && activities.length > 0) {
            console.log('Showing activity buttons with options:', activities);
            showInlineActivityButtons(activities);
            // Keep text input visible so users can type manually too
            textInputContainer.style.display = 'flex';
        }
    }
    
    // Also check if suggestions are sent directly (for backward compatibility)
    // BUT: Don't show if emoji_selector or reason_selector is requested
    if (data.suggestions && data.suggestions.length > 0 && 
        !elements.includes('activity_buttons') &&
        !elements.includes('emoji_selector') &&
        !elements.includes('reason_selector')) {
        console.log('Showing suggestions as activity buttons:', data.suggestions);
        showInlineActivityButtons(data.suggestions);
        textInputContainer.style.display = 'flex';
    }
    
    if (elements.includes('skip_button')) {
        skipContainer.style.display = 'block';
    }
    
    if (elements.includes('text_input')) {
        textInputContainer.style.display = 'flex';
        messageInput.focus();
    }
}

// Show emoji selector inline in the chat messages
function showInlineEmojiSelector() {
    const emojiContainer = document.createElement('div');
    emojiContainer.className = 'message assistant emoji-message inline-emoji-selector';
    emojiContainer.id = 'inline-emoji-selector';
    
    const emojiGrid = document.createElement('div');
    emojiGrid.className = 'inline-emoji-grid';
    
    const emojis = [
        { emoji: '😊', label: 'Awesome' },
        { emoji: '🙂', label: 'Pretty Good' },
        { emoji: '😐', label: 'Ok' },
        { emoji: '😟', label: 'Not Good' },
        { emoji: '😢', label: 'Horrible' }
    ];
    
    emojis.forEach(item => {
        const btn = document.createElement('button');
        btn.className = 'inline-emoji-btn';
        btn.innerHTML = `<span class="emoji-icon">${item.emoji}</span><span class="emoji-label">${item.label}</span>`;
        btn.onclick = () => {
            // Disable all emoji buttons
            emojiGrid.querySelectorAll('button').forEach(b => {
                b.disabled = true;
                b.classList.add('disabled');
            });
            
            // Highlight selected button
            btn.classList.remove('disabled');
            btn.classList.add('selected');
            btn.innerHTML = `<span class="emoji-icon">${item.emoji}</span><span class="emoji-label">✓ ${item.label}</span>`;
            
            sendMessage(item.emoji, `${item.emoji} ${item.label}`);
        };
        emojiGrid.appendChild(btn);
    });
    
    emojiContainer.appendChild(emojiGrid);
    chatMessages.appendChild(emojiContainer);
    scrollToBottom();
}

// Show reason selector inline
function showInlineReasonSelector(reasons) {
    const reasonContainer = document.createElement('div');
    reasonContainer.className = 'message assistant reason-message inline-reason-selector';
    
    const reasonGrid = document.createElement('div');
    reasonGrid.className = 'inline-reason-grid';
    
    reasons.forEach(reason => {
        const btn = document.createElement('button');
        btn.className = 'inline-reason-btn';
        btn.textContent = reason.label;
        btn.onclick = () => {
            // Disable all buttons in this grid
            reasonGrid.querySelectorAll('button').forEach(b => {
                b.disabled = true;
                b.classList.add('disabled');
            });
            
            // Highlight selected button
            btn.classList.remove('disabled');
            btn.classList.add('selected');
            btn.innerHTML = `✓ ${reason.label}`;
            
            sendMessage(reason.id, reason.label);
        };
        reasonGrid.appendChild(btn);
    });
    
    reasonContainer.appendChild(reasonGrid);
    chatMessages.appendChild(reasonContainer);
    scrollToBottom();
}

// Show generic buttons inline (NEW - for activity logging workflow)
function showInlineGenericButtons(buttons) {
    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'message assistant reason-message inline-generic-buttons';
    
    const buttonGrid = document.createElement('div');
    buttonGrid.className = 'inline-reason-grid';
    
    buttons.forEach(button => {
        const btn = document.createElement('button');
        btn.className = 'inline-reason-btn';
        btn.textContent = button.text;
        btn.onclick = () => {
            // Disable all buttons in this grid
            buttonGrid.querySelectorAll('button').forEach(b => {
                b.disabled = true;
                b.classList.add('disabled');
            });
            
            // Highlight selected button
            btn.classList.remove('disabled');
            btn.classList.add('selected');
            btn.innerHTML = `✓ ${button.text}`;
            
            // Send the action value (e.g., "log_activity_category:exercise")
            sendMessage(button.action, button.text);
        };
        buttonGrid.appendChild(btn);
    });
    
    buttonContainer.appendChild(buttonGrid);
    chatMessages.appendChild(buttonContainer);
    scrollToBottom();
}

// Show action buttons inline
function showInlineActionButtons(action) {
    const actionContainer = document.createElement('div');
    actionContainer.className = 'message assistant action-message inline-action-buttons';
    
    const actionCard = document.createElement('div');
    actionCard.className = 'action-card';
    
    actionCard.innerHTML = `
        <div class="action-details">
            <h4>${action.name}</h4>
            <p>${action.description}</p>
            <span class="action-meta">${action.duration} • ${action.effort} effort</span>
        </div>
        <div class="action-buttons-row">
            <button class="action-btn-yes" onclick="handleActionResponse('yes')">Start</button>
            <button class="action-btn-no" onclick="handleActionResponse('no')">Skip</button>
        </div>
    `;
    
    actionContainer.appendChild(actionCard);
    chatMessages.appendChild(actionContainer);
    scrollToBottom();
}

// Show multiple action buttons inline (NEW!)
function showInlineMultipleActionButtons(actions) {
    const actionContainer = document.createElement('div');
    actionContainer.className = 'message assistant action-message inline-action-buttons';
    
    const actionsGrid = document.createElement('div');
    actionsGrid.className = 'actions-grid';
    
    actions.forEach(action => {
        const actionCard = document.createElement('div');
        actionCard.className = 'action-card-compact';
        
        const actionBtn = document.createElement('button');
        actionBtn.className = 'action-btn-select';
        
        // Set button text based on action type
        if (action.action_type === 'open_external') {
            // Content items (blogs, videos, podcasts)
            const contentTypeMap = {
                'blog': 'Read',
                'video': 'Watch',
                'podcast': 'Listen'
            };
            const verb = contentTypeMap[action.content_type] || 'View';
            actionBtn.textContent = `${verb} ${action.name}`;
        } else {
            // Activity items
            actionBtn.textContent = `Start ${action.name}`;
        }
        
        actionBtn.onclick = () => {
            // Debug: Log the action object
            console.log('🔍 Action button clicked:', action);
            console.log('  - Has action.url?', !!action.url);
            console.log('  - Has action.content_url?', !!action.content_url);
            console.log('  - action_type:', action.action_type);
            
            // Check if action has a URL (like Listen to Music)
            if (action.url) {
                console.log('📍 Path: action.url');
                // Visual feedback and disable buttons
                actionBtn.classList.add('clicked');
                actionsGrid.querySelectorAll('.action-btn-select, .action-btn-skip').forEach(b => {
                    b.disabled = true;
                    b.classList.add('disabled');
                });
                actionBtn.classList.remove('disabled');
                actionBtn.classList.add('selected');
                
                // Show user's choice in chat
                const displayText = action.name;
                console.log('💬 Adding message:', `I want to ${displayText}`);
                addMessage('user', `I want to ${displayText}`);
                
                // Scroll to show message
                setTimeout(() => {
                    scrollToBottom();
                }, 100);
                
                // Open URL in new tab after delay
                setTimeout(() => {
                    console.log('🌐 Opening URL:', action.url);
                    window.open(action.url, '_blank');
                }, 200);
                
                // Track the interaction with backend
                const messageToSend = action.user_message || `I want to ${action.name}`;
                trackActivityStart(messageToSend, action);
                
                return;
            }
            
            // Check if this is external content (blog, video, podcast)
            if (action.action_type === 'open_external' && action.content_url) {
                console.log('External content clicked:', action);
                
                // Visual feedback and disable buttons
                actionBtn.classList.add('clicked');
                actionsGrid.querySelectorAll('.action-btn-select, .action-btn-skip').forEach(b => {
                    b.disabled = true;
                    b.classList.add('disabled');
                });
                actionBtn.classList.remove('disabled');
                actionBtn.classList.add('selected');
                
                // Show user's choice in chat
                const contentTypeMap = {
                    'blog': 'Read',
                    'video': 'Watch',
                    'podcast': 'Listen to'
                };
                const verb = contentTypeMap[action.content_type] || 'View';
                const displayText = `${verb} ${action.name}`;
                
                console.log('Adding user message:', displayText);
                addMessage('user', displayText);
                
                // Scroll to show the message
                setTimeout(() => {
                    scrollToBottom();
                }, 100);
                
                // Open external content in new tab after a brief delay
                setTimeout(() => {
                    console.log('Opening URL:', action.content_url);
                    window.open(action.content_url, '_blank');
                }, 200);
                
                // Track content click
                if (action.id && String(action.id).startsWith('content_')) {
                    fetch(`${API_BASE_URL}/chat/content/click`, {
                        method: 'POST',
                        headers: getAuthHeaders(),
                        body: JSON.stringify({ content_id: action.id })
                    }).catch(err => console.error('Failed to track content click:', err));
                }
                
                // Track the interaction with backend
                const messageToSend = action.user_message || `I want to ${action.name}`;
                trackActivityStart(messageToSend, action);
                
                return;
            }
            
            // Check if this is a module activity
            if (typeof isModuleActivity === 'function' && isModuleActivity(action)) {
                // Handle module activity
                handleModuleActivity(action);
                return;
            }
            
            // Check if these are engagement buttons (persistent shortcuts)
            const actionId = String(action.id); // Convert to string for .includes()
            const isEngagementButton = actionId.includes('log_') || actionId.includes('view_');
            
            if (isEngagementButton) {
                // For engagement buttons: Just show brief feedback, keep active
                actionBtn.classList.add('clicked');
                setTimeout(() => actionBtn.classList.remove('clicked'), 300);
            } else {
                // For one-time action buttons: Disable all after selection
                actionsGrid.querySelectorAll('.action-btn-select, .action-btn-skip').forEach(b => {
                    b.disabled = true;
                    b.classList.add('disabled');
                });
                
                // Highlight selected button
                actionBtn.classList.remove('disabled');
                actionBtn.classList.add('selected');
                actionBtn.innerHTML = `✓ Starting ${action.name}`;
            }
            
            // Send message with user-friendly display text
            const messageToSend = action.user_message || action.id;
            const displayText = action.name; // Show friendly name to user
            sendMessage(messageToSend, displayText);
        };
        
        actionCard.innerHTML = `
            <div class="action-header">
                <h4>${action.name}</h4>
                <span class="action-duration">${action.duration}</span>
            </div>
            <p class="action-description">${action.description}</p>
        `;
        actionCard.appendChild(actionBtn);
        
        actionsGrid.appendChild(actionCard);
    });
    
    // Add skip button (only for non-engagement contexts)
    const hasSkipOption = actions.some(a => {
        const actionId = String(a.id); // Convert to string for .includes()
        return !actionId.includes('log_') && !actionId.includes('view_');
    });
    if (hasSkipOption) {
        const skipCard = document.createElement('div');
        skipCard.className = 'action-card-compact skip-card';
        
        const skipBtn = document.createElement('button');
        skipBtn.className = 'action-btn-skip';
        skipBtn.textContent = 'Skip';
        
        skipBtn.onclick = () => {
            actionsGrid.querySelectorAll('.action-btn-select, .action-btn-skip').forEach(b => {
                b.disabled = true;
                b.classList.add('disabled');
            });
            skipBtn.classList.remove('disabled');
            skipBtn.classList.add('selected');
            skipBtn.innerHTML = '✓ Skipped';
            sendMessage('no');
        };
        
        skipCard.innerHTML = `
            <div class="action-header">
                <h4>Skip for now</h4>
            </div>
            <p class="action-description">I'll just log your mood</p>
        `;
        skipCard.appendChild(skipBtn);
        
        actionsGrid.appendChild(skipCard);
    }
    
    actionContainer.appendChild(actionsGrid);
    chatMessages.appendChild(actionContainer);
    scrollToBottom();
}

// Track activity start without waiting for response (for external content)
async function trackActivityStart(message, action) {
    try {
        await fetch(`${API_BASE_URL}/chat/message`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                message: message
            })
        });
        
        // Store pending activity for follow-up when user returns
        if (action.id) {
            localStorage.setItem('pending_activity', JSON.stringify({
                activity_id: action.id,
                activity_name: action.name,
                activity_type: action.action_type || 'open_external',
                content_type: action.content_type || 'video',
                timestamp: Date.now()
            }));
        }
    } catch (error) {
        console.error('Error tracking activity start:', error);
    }
}

// Handle action response
function handleActionResponse(response) {
    const actionContainer = document.querySelector('.inline-action-buttons');
    if (actionContainer) {
        actionContainer.remove();
    }
    sendMessage(response);
}

// Show activity buttons inline (NEW!)
function showInlineActivityButtons(activities) {
    console.log('showInlineActivityButtons called with:', activities);
    
    const activityContainer = document.createElement('div');
    activityContainer.className = 'message assistant activity-message inline-activity-buttons';
    activityContainer.id = 'latest-activity-buttons'; // Add ID for easy reference
    
    const activityGrid = document.createElement('div');
    activityGrid.className = 'activity-grid';
    
    activities.forEach((activity, index) => {
        console.log(`Processing activity ${index}:`, activity);
        
        const btn = document.createElement('button');
        btn.className = 'activity-btn';
        
        // Handle different field names from backend
        const activityId = activity.id || activity.suggestion_key || activity.activity_id;
        const label = activity.name || activity.label || activity.title || activityId || 'Unknown';
        const userMessage = activity.user_message || label;
        
        btn.innerHTML = `<span class="activity-label">${label}</span>`;
        
        btn.onclick = () => {
            // Check if this is a logging button (should be clickable multiple times)
            const isLoggingButton = activityId.startsWith('log_');
            
            // For non-logging buttons, prevent multiple clicks
            if (!isLoggingButton && btn.classList.contains('selected')) {
                return;
            }
            
            // For logging buttons, allow multiple clicks but provide visual feedback
            if (isLoggingButton) {
                // Add temporary "clicked" animation
                btn.classList.add('clicked');
                btn.style.transform = 'scale(0.95)';
                setTimeout(() => {
                    btn.classList.remove('clicked');
                    btn.style.transform = 'scale(1)';
                }, 200);
                
                // Don't add permanent "selected" state for logging buttons
                // Just send the message and allow clicking again
                sendMessage(activityId, `Logging ${label}`);
                return;
            }
            
            // For non-logging buttons, mark as selected (one-time use)
            btn.classList.add('selected');
            btn.innerHTML = `<span class="activity-label">✓ ${label}</span>`;
            
            // Brief animation
            btn.style.transform = 'scale(0.95)';
            setTimeout(() => {
                btn.style.transform = 'scale(1)';
            }, 150);
            
            // Track activity start for follow-up
            const activityState = {
                activity_id: activityId,
                activity_name: label,
                activity_type: activity.action_type || 'regular',
                timestamp: Date.now(),
                completed: false
            };
            
            // Handle different action types
            if (activity.action_type === 'open_external' && activity.content_url) {
                // External content (blog, video, podcast)
                console.log('Opening external URL:', activity.content_url);
                
                // Save state for follow-up
                activityState.content_url = activity.content_url;
                activityState.content_type = activity.content_type || 'content';
                localStorage.setItem('pending_activity', JSON.stringify(activityState));
                
                // Open external link
                window.open(activity.content_url, '_blank');
                
                // Send message to backend (hidden from UI)
                sendMessage(`start_${activityId}`, null);
                
            } else if (activity.is_module || activityId.includes('_module')) {
                // Module activity (meditation, workout, outdoor)
                console.log('Triggering module:', activityId);
                
                // Save state for follow-up (using existing module system)
                localStorage.setItem('pending_module', JSON.stringify(activityState));
                
                const moduleName = activityId.replace('_module', '');
                triggerModule(moduleName, label);
                
                // Send message to backend (hidden from UI)
                sendMessage(`start_${activityId}`, null);
                
            } else {
                // Regular activity (breathing, stretching, journaling, etc.)
                // BUT: Don't save pending activity for logging buttons (log_water, log_mood, etc.)
                const isLoggingButton = activityId.startsWith('log_');
                
                if (!isLoggingButton) {
                    // Save state for follow-up (only for actual activities, not logging)
                    localStorage.setItem('pending_activity', JSON.stringify(activityState));
                }
                
                // Send message based on button type
                if (isLoggingButton) {
                    // For logging buttons, send the ID directly for fast routing
                    sendMessage(activityId, `Starting ${label}`);
                } else {
                    // For activity buttons, send natural language
                    sendMessage(`I want to ${activityId}`, `Starting ${label}`);
                }
            }
        };
        
        activityGrid.appendChild(btn);
    });
    
    activityContainer.appendChild(activityGrid);
    chatMessages.appendChild(activityContainer);
    scrollToBottom();
    
    // Track the location of the latest activity buttons
    lastActivityButtonsLocation = activityContainer;
    
    // Show pin button after activity buttons are created
    setTimeout(() => {
        showPinButton();
    }, 1000);
}

// Add message to chat
function addMessage(role, text, extraClass = '') {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role} ${extraClass}`;
    
    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'message-bubble';
    bubbleDiv.textContent = text;
    
    messageDiv.appendChild(bubbleDiv);
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

// Show typing indicator
function showTypingIndicator() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.id = `typing-${Date.now()}`;
    
    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing-indicator';
    typingDiv.innerHTML = '<span></span><span></span><span></span>';
    
    messageDiv.appendChild(typingDiv);
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
    
    return messageDiv.id;
}

// Remove typing indicator
function removeTypingIndicator(id) {
    const element = document.getElementById(id);
    if (element) {
        element.remove();
    }
}






// ============================================================================
// ACTIVITY FOLLOW-UP SYSTEM
// ============================================================================

/**
 * Check if user is returning from an external activity or simple activity
 * and follow up with them about it
 */
function checkPendingActivity() {
    const pending = localStorage.getItem('pending_activity');
    
    if (!pending) {
        return;
    }
    
    try {
        const activityData = JSON.parse(pending);
        
        // Check how long ago the activity was started
        const timeSince = Date.now() - activityData.timestamp;
        const secondsSince = Math.floor(timeSince / 1000);
        const minutesSince = Math.floor(timeSince / 60000);
        
        // Only follow up if activity was started recently (within 60 minutes)
        if (minutesSince > 60) {
            // Too long ago - clear it
            localStorage.removeItem('pending_activity');
            return;
        }
        
        // If user returns too quickly (< 5 seconds), don't follow up yet
        // They probably just accidentally closed the tab or are still loading
        if (secondsSince < 5) {
            console.log('User returned too quickly, keeping pending activity for later');
            return; // Keep the pending activity, don't clear it
        }
        
        // Clear the pending state
        localStorage.removeItem('pending_activity');
        
        // Follow up based on activity type
        if (activityData.activity_type === 'open_external') {
            // External content (blog, video, podcast)
            
            // Send message to backend to trigger workflow follow-up
            // Don't show this internal message in the UI (pass null as displayMessage)
            setTimeout(() => {
                sendMessage('returned_from_external_activity', null);
            }, 1000);
            
        } else {
            // Regular activity (breathing, stretching, etc.)
            setTimeout(() => {
                // Send message to backend to trigger workflow follow-up
                sendMessage('returned_from_activity', null);
            }, 1000);
        }
        
    } catch (e) {
        console.error('Error checking pending activity:', e);
        localStorage.removeItem('pending_activity');
    }
}

/**
 * Show feedback buttons for external content
 */
function showActivityFeedbackButtons(activityData) {
    const feedbackContainer = document.createElement('div');
    feedbackContainer.className = 'message assistant feedback-message inline-feedback-buttons';
    
    const feedbackGrid = document.createElement('div');
    feedbackGrid.className = 'inline-feedback-grid';
    
    const feedbackOptions = [
        { id: 'helpful', label: '👍 Helpful', emoji: '👍' },
        { id: 'not_helpful', label: '👎 Not helpful', emoji: '👎' },
        { id: 'skip_feedback', label: 'Skip', emoji: '' }
    ];
    
    feedbackOptions.forEach(option => {
        const btn = document.createElement('button');
        btn.className = 'inline-feedback-btn';
        btn.textContent = option.label;
        
        btn.onclick = () => {
            // Disable all buttons
            feedbackGrid.querySelectorAll('button').forEach(b => {
                b.disabled = true;
                b.classList.add('disabled');
            });
            
            // Highlight selected button with enhanced styling
            btn.classList.remove('disabled');
            btn.classList.add('selected');
            btn.textContent = option.label; // Keep original text, checkmark added via CSS
            
            // Scroll to ensure the selected button is visible
            setTimeout(() => {
                btn.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }, 100);
            
            // Send feedback
            if (option.id === 'skip_feedback') {
                sendMessage('skip', 'Skip');
            } else {
                const feedbackMessage = option.id === 'helpful' 
                    ? `Yes, "${activityData.activity_name}" was helpful`
                    : `No, "${activityData.activity_name}" wasn't helpful`;
                
                sendMessage(option.id, feedbackMessage);
            }
        };
        
        feedbackGrid.appendChild(btn);
    });
    
    feedbackContainer.appendChild(feedbackGrid);
    chatMessages.appendChild(feedbackContainer);
    scrollToBottom();
}

/**
 * Helper function to scroll chat to bottom
 */
function scrollToBottom() {
    if (chatMessages) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

// ============================================================================
// PIN BUTTON - SIMPLE IN-CHAT NAVIGATION TO ACTIVITY BUTTONS
// ============================================================================

/**
 * Show pin button above text input when activity buttons are scrolled out of view
 * Places the button in the marked area as requested
 */
function showPinButton() {
    // Don't show if user not authenticated
    if (!currentUser) {
        return;
    }
    
    // Don't show if jump is in progress
    if (window.jumpInProgress) {
        return;
    }
    
    // Find all activity buttons in the chat
    const allActivityButtons = document.querySelectorAll('.inline-activity-buttons');
    
    if (allActivityButtons.length === 0) {
        // No activity buttons exist, don't show pin button
        return;
    }
    
    // Get the most recent activity buttons
    const mostRecentActivityButtons = allActivityButtons[allActivityButtons.length - 1];
    
    // Update our stored reference
    lastActivityButtonsLocation = mostRecentActivityButtons;
    
    // Check if the most recent activity buttons are currently visible in viewport
    const rect = mostRecentActivityButtons.getBoundingClientRect();
    const chatRect = chatMessages.getBoundingClientRect();
    
    // More generous visibility check - consider partially visible as visible
    const isVisible = rect.bottom > chatRect.top && rect.top < chatRect.bottom;
    const isFullyVisible = rect.top >= chatRect.top && rect.bottom <= chatRect.bottom;
    
    console.log('Activity buttons visibility check:', {
        isVisible,
        isFullyVisible,
        rectTop: rect.top,
        rectBottom: rect.bottom,
        chatTop: chatRect.top,
        chatBottom: chatRect.bottom
    });
    
    // Only show pin button if activity buttons are not visible at all
    if (isVisible) {
        // Remove existing pin button if activity buttons are visible
        const existingPin = document.getElementById('pinButton');
        if (existingPin) {
            existingPin.remove();
        }
        return;
    }
    
    // Remove existing pin button if present (to avoid duplicates)
    const existingPin = document.getElementById('pinButton');
    if (existingPin) {
        return; // Already showing, don't create another
    }
    
    // Create pin button above text input (in the marked area)
    const pinButton = document.createElement('div');
    pinButton.id = 'pinButton';
    pinButton.className = 'quick-actions-bar';
    pinButton.innerHTML = `
        <div class="quick-actions-button" onclick="jumpToActivityButtons()">
            <span class="quick-actions-icon">⚡</span>
            <span class="quick-actions-text">Quick Actions</span>
            <span class="quick-actions-arrow">↑</span>
        </div>
    `;
    
    // Insert above text input container
    const textInputContainer = document.getElementById('textInputContainer');
    if (textInputContainer && textInputContainer.parentNode) {
        textInputContainer.parentNode.insertBefore(pinButton, textInputContainer);
    }
}

/**
 * Jump directly to the most recent activity buttons with smart detection
 * Make this function globally accessible and more reliable
 */
window.jumpToActivityButtons = function() {
    console.log('jumpToActivityButtons called');
    
    // Prevent multiple rapid clicks
    if (window.jumpInProgress) {
        console.log('Jump already in progress, ignoring click');
        return;
    }
    
    window.jumpInProgress = true;
    
    // First, try to find the most recent activity buttons in the chat
    const allActivityButtons = document.querySelectorAll('.inline-activity-buttons');
    let targetActivityButtons = null;
    
    if (allActivityButtons.length > 0) {
        // Get the last (most recent) activity buttons
        targetActivityButtons = allActivityButtons[allActivityButtons.length - 1];
        console.log('Found activity buttons via querySelector:', targetActivityButtons);
    } else if (lastActivityButtonsLocation) {
        // Fallback to stored reference
        targetActivityButtons = lastActivityButtonsLocation;
        console.log('Using stored lastActivityButtonsLocation:', targetActivityButtons);
    }
    
    if (!targetActivityButtons) {
        console.log('No activity buttons found to scroll to');
        window.jumpInProgress = false;
        return;
    }
    
    // Update the stored reference to the most recent one
    lastActivityButtonsLocation = targetActivityButtons;
    
    console.log('Scrolling to activity buttons:', targetActivityButtons);
    
    // Remove the pin button immediately to prevent double-clicks
    const pinButton = document.getElementById('pinButton');
    if (pinButton) {
        pinButton.remove();
    }
    
    // Smooth scroll to the activity buttons
    targetActivityButtons.scrollIntoView({
        behavior: 'smooth',
        block: 'center'
    });
    
    // Add highlight effect to show where we jumped
    targetActivityButtons.classList.add('highlighted');
    
    // Use a more reliable method to detect scroll completion
    let scrollCheckCount = 0;
    const maxScrollChecks = 20; // Maximum checks (2 seconds at 100ms intervals)
    
    const checkScrollComplete = () => {
        scrollCheckCount++;
        
        // Check if activity buttons are now visible
        const rect = targetActivityButtons.getBoundingClientRect();
        const chatRect = chatMessages.getBoundingClientRect();
        const isVisible = rect.top >= chatRect.top && rect.bottom <= chatRect.bottom;
        
        if (isVisible || scrollCheckCount >= maxScrollChecks) {
            // Scroll is complete or we've waited long enough
            console.log('Scroll completed, activity buttons visible:', isVisible);
            
            if (targetActivityButtons) {
                targetActivityButtons.classList.remove('highlighted');
            }
            
            // Reset jump progress after a longer delay to prevent immediate re-showing of pin button
            setTimeout(() => {
                window.jumpInProgress = false;
                
                // Only check for pin button after user has had time to interact with activity buttons
                setTimeout(() => {
                    if (isChatOpen) {
                        showPinButton();
                    }
                }, 3000); // Wait 3 seconds before checking if pin button should reappear
            }, 500);
        } else {
            // Continue checking
            setTimeout(checkScrollComplete, 100);
        }
    };
    
    // Start checking after a brief delay to allow scroll animation to begin
    setTimeout(checkScrollComplete, 200);
};

/**
 * Check scroll position and show pin button if needed
 */
function handleChatScroll() {
    if (!isChatOpen || !currentUser) {
        return;
    }
    
    // Debounce scroll events
    clearTimeout(window.scrollCheckTimeout);
    window.scrollCheckTimeout = setTimeout(() => {
        showPinButton();
    }, 200); // Reduced delay for more responsive behavior
}

// Add scroll listener to chat messages
if (chatMessages) {
    chatMessages.addEventListener('scroll', handleChatScroll);
}

/**
 * Show simple feedback buttons (cleaner UI for yes/no/skip)
 */
function showSimpleFeedbackButtons(actions) {
    const container = document.createElement('div');
    container.className = 'simple-feedback-container';
    container.style.cssText = 'display: flex; gap: 8px; margin: 10px 0; flex-wrap: wrap;';
    
    actions.forEach(action => {
        const btn = document.createElement('button');
        btn.className = 'simple-feedback-btn';
        btn.textContent = action.name;
        btn.style.cssText = `
            flex: 1;
            min-width: 100px;
            padding: 12px 20px;
            border: 2px solid #667eea;
            border-radius: 12px;
            background: white;
            color: #667eea;
            font-size: 15px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
        `;
        
        btn.onmouseover = () => {
            if (!btn.disabled) {
                btn.style.background = '#667eea';
                btn.style.color = 'white';
                btn.style.transform = 'translateY(-2px)';
                btn.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.3)';
            }
        };
        
        btn.onmouseout = () => {
            if (!btn.disabled && !btn.classList.contains('selected')) {
                btn.style.background = 'white';
                btn.style.color = '#667eea';
                btn.style.transform = 'translateY(0)';
                btn.style.boxShadow = 'none';
            }
        };
        
        btn.onclick = () => {
            // Disable all buttons
            container.querySelectorAll('button').forEach(b => {
                b.disabled = true;
                b.style.opacity = '0.5';
                b.style.cursor = 'not-allowed';
            });
            
            // Highlight selected
            btn.classList.add('selected');
            btn.style.opacity = '1';
            btn.style.background = '#48bb78';
            btn.style.borderColor = '#48bb78';
            btn.style.color = 'white';
            btn.style.transform = 'scale(1.05)';
            
            // Send message with user-friendly display text
            sendMessage(action.id, action.name);
        };
        
        container.appendChild(btn);
    });
    
    chatMessages.appendChild(container);
    scrollToBottom();
}
