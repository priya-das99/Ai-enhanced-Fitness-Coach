/**
 * Module Integration for Chat Assistant
 * Handles external module activities (Outdoor, Workout, Meditation)
 */

// Module Routes Configuration
const MODULE_ROUTES = {
    'outdoor_activity': '/outdoor',
    'seven_minute_workout': '/workout',
    'squats_workout': '/workout',  // Same workout page
    'meditation_module': '/meditation'
};

/**
 * Check if returning from a module on page load
 */
function checkModuleCompletion() {
    const pending = localStorage.getItem('pending_module');
    
    if (pending) {
        try {
            const moduleData = JSON.parse(pending);
            
            // Check if module was completed
            if (moduleData.completed) {
                // Show completion message
                displayBotMessage(`Great job completing ${moduleData.activity_name}! 🎉`);
                displayBotMessage("How are you feeling now?");
                
                // Clear the pending state
                localStorage.removeItem('pending_module');
                
                // Show mood selector or continue conversation
                showMoodButtons();
            } else {
                // Module was started but not completed
                const timeSince = Date.now() - moduleData.timestamp;
                const minutesSince = Math.floor(timeSince / 60000);
                
                if (minutesSince < 30) {
                    // Recently started - ask if they want to continue
                    displayBotMessage(`I see you started ${moduleData.activity_name} ${minutesSince} minutes ago.`);
                    displayBotMessage("Would you like to continue or try something else?");
                    
                    // Show options
                    showModuleResumeOptions(moduleData);
                } else {
                    // Too long ago - clear it
                    localStorage.removeItem('pending_module');
                }
            }
        } catch (e) {
            console.error('Error checking module completion:', e);
            localStorage.removeItem('pending_module');
        }
    }
}

/**
 * Show options to resume or skip abandoned module
 */
function showModuleResumeOptions(moduleData) {
    const options = [
        {
            id: 'resume_module',
            name: `Resume ${moduleData.activity_name}`,
            user_message: `Resume ${moduleData.activity_name}`,
            module_data: moduleData
        },
        {
            id: 'skip_module',
            name: 'Try something else',
            user_message: 'Try something else'
        }
    ];
    
    showInlineMultipleActionButtons(options);
}

/**
 * Handle module activity button click
 */
function handleModuleActivity(action) {
    console.log('Handling module activity:', action);
    
    // Save state before navigating
    const moduleState = {
        activity_id: action.id,
        activity_name: action.name,
        timestamp: Date.now(),
        completed: false,
        mood: getCurrentMood(),  // Save current mood context
        reason: getCurrentReason()  // Save current reason
    };
    
    localStorage.setItem('pending_module', JSON.stringify(moduleState));
    
    // Send message to chat
    displayUserMessage(action.user_message || `Start ${action.name}`);
    
    // Show transition message
    displayBotMessage(`Opening ${action.name}...`);
    
    // Navigate to module after brief delay
    const route = MODULE_ROUTES[action.id];
    if (route) {
        setTimeout(() => {
            window.location.href = route;
        }, 800);
    } else {
        console.error('No route found for module:', action.id);
        displayBotMessage(`Sorry, the ${action.name} module is not available yet.`);
        localStorage.removeItem('pending_module');
    }
}

/**
 * Check if an action is a module activity
 */
function isModuleActivity(action) {
    return action.is_module === true || 
           action.module_type === 'external' ||
           MODULE_ROUTES.hasOwnProperty(action.id);
}

/**
 * Get current mood from state (helper)
 */
function getCurrentMood() {
    // Try to get from recent messages or state
    const messages = chatMessages.querySelectorAll('.message.user');
    for (let i = messages.length - 1; i >= 0; i--) {
        const text = messages[i].textContent;
        // Check if it's an emoji
        if (/[\u{1F600}-\u{1F64F}]/u.test(text)) {
            return text.trim();
        }
    }
    return null;
}

/**
 * Get current reason from state (helper)
 */
function getCurrentReason() {
    // Try to get from recent messages
    const messages = chatMessages.querySelectorAll('.message.user');
    for (let i = messages.length - 1; i >= 0; i--) {
        const text = messages[i].textContent.toLowerCase();
        // Check if it looks like a reason (not an emoji, not a yes/no)
        if (text.length > 3 && !['yes', 'no', 'skip'].includes(text)) {
            return messages[i].textContent.trim();
        }
    }
    return null;
}

/**
 * Show mood buttons after module completion
 */
function showMoodButtons() {
    const moods = [
        { emoji: '😊', label: 'Better' },
        { emoji: '😐', label: 'Same' },
        { emoji: '😢', label: 'Worse' }
    ];
    
    const moodContainer = document.createElement('div');
    moodContainer.className = 'message assistant inline-emoji-selector';
    
    const moodGrid = document.createElement('div');
    moodGrid.className = 'emoji-grid';
    
    moods.forEach(mood => {
        const btn = document.createElement('button');
        btn.className = 'emoji-btn';
        btn.innerHTML = `
            <span class="emoji">${mood.emoji}</span>
            <span class="emoji-label">${mood.label}</span>
        `;
        btn.onclick = () => {
            sendMessage(mood.emoji);
            moodContainer.remove();
        };
        moodGrid.appendChild(btn);
    });
    
    moodContainer.appendChild(moodGrid);
    chatMessages.appendChild(moodContainer);
    scrollToBottom();
}

/**
 * Display bot message (helper)
 */
function displayBotMessage(text) {
    if (typeof addMessage === 'function') {
        addMessage('assistant', text);
    } else {
        console.log('Bot:', text);
    }
}

/**
 * Display user message (helper)
 */
function displayUserMessage(text) {
    if (typeof addMessage === 'function') {
        addMessage('user', text);
    } else {
        console.log('User:', text);
    }
}

/**
 * Scroll to bottom (helper)
 */
function scrollToBottom() {
    if (chatMessages) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

// Export functions for use in chat.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        checkModuleCompletion,
        handleModuleActivity,
        isModuleActivity,
        MODULE_ROUTES
    };
}
