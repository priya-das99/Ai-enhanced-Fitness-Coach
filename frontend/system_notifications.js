// system_notifications.js
// Polls for new system notifications and displays them in chat

const NOTIFICATION_CHECK_INTERVAL = 30000; // Check every 30 seconds
let lastNotificationCheck = null;
let notificationCheckInterval = null;
let shownNotificationIds = new Set(); // Track which notifications we've already shown

// Start checking for notifications
function startNotificationPolling() {
    if (notificationCheckInterval) {
        clearInterval(notificationCheckInterval);
    }
    
    // Check immediately
    checkForNewNotifications();
    
    // Then check every 30 seconds
    notificationCheckInterval = setInterval(() => {
        checkForNewNotifications();
    }, NOTIFICATION_CHECK_INTERVAL);
    
    console.log('✅ Notification polling started (checking every 30 seconds)');
}

// Stop checking for notifications
function stopNotificationPolling() {
    if (notificationCheckInterval) {
        clearInterval(notificationCheckInterval);
        notificationCheckInterval = null;
    }
    console.log('❌ Notification polling stopped');
}

// Check for new system notifications
async function checkForNewNotifications() {
    if (!currentUser) return;
    
    try {
        // Check both the old endpoint and new chat messages endpoint
        let response = await fetch(`${API_BASE_URL}/chat/messages`, {
            headers: getAuthHeaders()
        });
        
        if (!response.ok) {
            // Fallback to old endpoint
            response = await fetch(`${API_BASE_URL}/chat/system-notifications`, {
                headers: getAuthHeaders()
            });
        }
        
        if (!response.ok) {
            console.error('Failed to fetch notifications:', response.status);
            return;
        }
        
        const data = await response.json();
        
        // Handle both response formats
        let notifications = [];
        
        if (data.notifications) {
            // Old format
            notifications = data.notifications;
        } else if (data.messages) {
            // New format - filter for system messages
            notifications = data.messages
                .filter(msg => msg.sender === 'system')
                .filter(msg => {
                    // Only show recent notifications (last 5 minutes)
                    const msgTime = new Date(msg.timestamp);
                    const now = new Date();
                    const diffMinutes = (now - msgTime) / (1000 * 60);
                    return diffMinutes <= 5;
                })
                .filter(msg => !shownNotificationIds.has(msg.id)) // Only show new ones
                .map(msg => ({
                    id: msg.id,
                    title: extractNotificationTitle(msg.message),
                    message: msg.message,
                    timestamp: msg.timestamp,
                    action_buttons: generateActionButtons(msg.message)
                }));
        }
        
        if (notifications.length > 0) {
            console.log(`📬 Found ${notifications.length} new notification(s)`);
            
            // Display each notification and mark as shown
            notifications.forEach(notification => {
                displaySystemNotification(notification);
                shownNotificationIds.add(notification.id); // Mark as shown
            });
        }
        
        lastNotificationCheck = new Date();
        
    } catch (error) {
        console.error('Error checking for notifications:', error);
    }
}

// Extract notification title from content
function extractNotificationTitle(content) {
    const lowerContent = content.toLowerCase();
    
    if (lowerContent.includes('water') || lowerContent.includes('hydration')) {
        return '💧 Hydration Reminder';
    } else if (lowerContent.includes('exercise') || lowerContent.includes('workout')) {
        return '🏃 Exercise Reminder';
    } else if (lowerContent.includes('mood')) {
        return '😊 Mood Check-in';
    } else if (lowerContent.includes('sleep')) {
        return '😴 Sleep Reminder';
    } else if (lowerContent.includes('challenge')) {
        return '🎯 Challenge Reminder';
    } else {
        return '💡 System Notification';
    }
}

// Generate action buttons based on content
function generateActionButtons(content) {
    const lowerContent = content.toLowerCase();
    
    if (lowerContent.includes('water') || lowerContent.includes('hydration')) {
        return [
            { id: 'log_water', label: '💧 Log Water' },
            { id: 'remind_later', label: '⏰ Remind Later' },
            { id: 'view_progress', label: '📊 View Progress' }
        ];
    } else if (lowerContent.includes('exercise') || lowerContent.includes('workout')) {
        return [
            { id: 'log_exercise', label: '🏃 Log Exercise' },
            { id: 'start_workout', label: '💪 Start Workout' }
        ];
    } else if (lowerContent.includes('mood')) {
        return [
            { id: 'log_mood', label: '😊 Log Mood' },
            { id: 'mood_great', label: '😄 Great' },
            { id: 'mood_okay', label: '😐 Okay' }
        ];
    } else {
        return [
            { id: 'acknowledge', label: '✓ Got it' }
        ];
    }
}

// Display a system notification in the chat
function displaySystemNotification(notification) {
    // Create the main notification container
    const notificationDiv = document.createElement('div');
    
    // Determine notification type for styling
    const notificationType = getNotificationType(notification.message);
    notificationDiv.className = `system-notification ${notificationType ? `notification-${notificationType}` : ''} pulse`;
    
    // Create the notification content (matching the HTML design exactly)
    notificationDiv.innerHTML = `
        <div class="notification-header">
            <div class="notification-icon">${getNotificationEmoji(notification.message)}</div>
            <div class="notification-title">${notification.title || extractNotificationTitle(notification.message)}</div>
            <div class="notification-time">${formatNotificationTime(notification.timestamp)}</div>
        </div>
        <div class="notification-message">
            ${cleanNotificationMessage(notification.message)}
        </div>
        ${notification.action_buttons && notification.action_buttons.length > 0 ? `
            <div class="notification-actions">
                ${notification.action_buttons.map(button => 
                    `<button class="notification-btn ${button.id === notification.action_buttons[0].id ? 'primary' : ''}" 
                             onclick="handleNotificationAction('${button.id}')">
                        ${button.label}
                    </button>`
                ).join('')}
            </div>
        ` : ''}
    `;
    
    // Add to chat messages
    chatMessages.appendChild(notificationDiv);
    
    // Remove pulse animation after 2 seconds
    setTimeout(() => notificationDiv.classList.remove('pulse'), 2000);
    
    // Scroll to show notification
    scrollToBottom();
    
    // Show badge if chat is closed
    if (!isChatOpen) {
        showNewMessageBadge();
    }
}

// Handle notification action button click
function handleNotificationAction(actionId) {
    console.log('Notification action clicked:', actionId);
    
    // Map action IDs to messages that work with your chat system
    const actionMap = {
        'log_water': 'I want to log water',
        'log_mood': 'I want to log my mood',
        'log_exercise': 'I want to log exercise',
        'log_sleep': 'I want to log sleep',
        'remind_later': 'Remind me later',
        'view_progress': 'Show my progress',
        'start_workout': 'I want to start a workout',
        'mood_great': 'I feel great 😄',
        'mood_okay': 'I feel okay 😐',
        'acknowledge': 'Got it, thanks!'
    };
    
    const message = actionMap[actionId] || actionId;
    
    // Send the message through your chat system
    if (typeof sendMessage === 'function') {
        sendMessage(message);
    } else {
        // Fallback: try to find and use the chat input
        const chatInput = document.querySelector('input[type="text"]') || 
                         document.querySelector('.chat-input input') ||
                         document.querySelector('#message-input');
        
        if (chatInput) {
            chatInput.value = message;
            chatInput.focus();
            
            // Try to trigger send
            const sendBtn = document.querySelector('.send-btn') || 
                           document.querySelector('button[type="submit"]') ||
                           document.querySelector('.chat-send-button');
            
            if (sendBtn) {
                sendBtn.click();
            } else {
                // Trigger enter key
                const enterEvent = new KeyboardEvent('keypress', {
                    key: 'Enter',
                    code: 'Enter',
                    keyCode: 13,
                    bubbles: true
                });
                chatInput.dispatchEvent(enterEvent);
            }
        }
    }
}

// Show badge on chatbot button
function showNewMessageBadge() {
    if (chatbotBadge) {
        chatbotBadge.style.display = 'block';
        hasNewMessage = true;
    }
}

// Hide badge when chat is opened
function hideNewMessageBadge() {
    if (chatbotBadge) {
        chatbotBadge.style.display = 'none';
        hasNewMessage = false;
    }
}

// Helper functions for enhanced design
function getNotificationType(content) {
    const lowerContent = content.toLowerCase();
    
    if (lowerContent.includes('water') || lowerContent.includes('hydration')) {
        return 'water';
    } else if (lowerContent.includes('exercise') || lowerContent.includes('workout')) {
        return 'exercise';
    } else if (lowerContent.includes('mood')) {
        return 'mood';
    } else if (lowerContent.includes('sleep')) {
        return 'sleep';
    } else if (lowerContent.includes('challenge')) {
        return 'challenge';
    }
    return null;
}

function getNotificationEmoji(content) {
    const lowerContent = content.toLowerCase();
    
    if (lowerContent.includes('water') || lowerContent.includes('hydration')) {
        return '💧';
    } else if (lowerContent.includes('exercise') || lowerContent.includes('workout')) {
        return '🏃';
    } else if (lowerContent.includes('mood')) {
        return '😊';
    } else if (lowerContent.includes('sleep')) {
        return '😴';
    } else if (lowerContent.includes('challenge')) {
        return '🎯';
    } else {
        return '💡';
    }
}

function formatNotificationTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit',
        hour12: true 
    });
}

function cleanNotificationMessage(message) {
    // Remove the title prefix if it exists (e.g., "💡 🧪 Test Notification")
    const lines = message.split('\n');
    if (lines.length > 1 && lines[0].includes('💡')) {
        return lines.slice(2).join('\n').trim(); // Skip title and empty line
    }
    return message;
}

// Export functions for use in chat.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        startNotificationPolling,
        stopNotificationPolling,
        checkForNewNotifications
    };
}
