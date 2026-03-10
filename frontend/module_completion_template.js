/**
 * Module Completion Template
 * Add this code to your module pages (workout.html, meditation.html, outdoor.html)
 */

// Configuration - Load from config.js
const API_BASE_URL = window.API_CONFIG?.API_BASE_URL || 'http://localhost:8000/api/v1';

/**
 * Call this function when user completes the module
 * @param {string} moduleId - The module identifier (e.g., '7min_workout')
 * @param {number} durationMinutes - How long the activity took
 * @param {object} additionalData - Any extra data (optional)
 */
async function onModuleComplete(moduleId, durationMinutes, additionalData = {}) {
    console.log('Module completed:', moduleId);
    
    // Get pending module info
    const pending = localStorage.getItem('pending_module');
    
    if (pending) {
        try {
            const moduleData = JSON.parse(pending);
            
            // Log the activity to backend
            await logModuleActivity(moduleData.activity_id, durationMinutes, additionalData);
            
            // Mark as completed
            moduleData.completed = true;
            moduleData.completed_at = Date.now();
            moduleData.duration_minutes = durationMinutes;
            
            // Save updated state
            localStorage.setItem('pending_module', JSON.stringify(moduleData));
            
            // Show success message
            showCompletionMessage(moduleData.activity_name);
            
            // Return to chat after brief delay
            setTimeout(() => {
                window.location.href = '/';  // or '/chat' depending on your routing
            }, 1500);
            
        } catch (e) {
            console.error('Error completing module:', e);
            // Still return to chat even if logging fails
            setTimeout(() => {
                window.location.href = '/';
            }, 1000);
        }
    } else {
        console.warn('No pending module found');
        // Just return to chat
        window.location.href = '/';
    }
}

/**
 * Log activity to backend
 */
async function logModuleActivity(activityId, durationMinutes, additionalData) {
    const token = localStorage.getItem('token');
    
    if (!token) {
        console.warn('No auth token found');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/activity/log`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                activity_type: activityId,
                quantity: durationMinutes,
                unit: 'minutes',
                notes: `Completed via module`,
                ...additionalData
            })
        });
        
        if (response.ok) {
            console.log('Activity logged successfully');
        } else {
            console.error('Failed to log activity:', response.status);
        }
    } catch (error) {
        console.error('Error logging activity:', error);
    }
}

/**
 * Show completion message
 */
function showCompletionMessage(activityName) {
    // Create overlay
    const overlay = document.createElement('div');
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.8);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9999;
    `;
    
    // Create message
    const message = document.createElement('div');
    message.style.cssText = `
        background: white;
        padding: 2rem;
        border-radius: 1rem;
        text-align: center;
        max-width: 400px;
    `;
    
    message.innerHTML = `
        <div style="font-size: 4rem; margin-bottom: 1rem;">🎉</div>
        <h2 style="margin-bottom: 0.5rem;">Great Job!</h2>
        <p style="color: #666;">You completed ${activityName}</p>
        <p style="color: #999; font-size: 0.9rem; margin-top: 1rem;">Returning to chat...</p>
    `;
    
    overlay.appendChild(message);
    document.body.appendChild(overlay);
}

/**
 * Call this if user cancels/exits without completing
 */
function onModuleCancel() {
    console.log('Module cancelled');
    
    // Clear pending state
    localStorage.removeItem('pending_module');
    
    // Return to chat
    window.location.href = '/';
}

/**
 * Get module info (useful for displaying in module UI)
 */
function getModuleInfo() {
    const pending = localStorage.getItem('pending_module');
    
    if (pending) {
        try {
            return JSON.parse(pending);
        } catch (e) {
            console.error('Error parsing module info:', e);
            return null;
        }
    }
    
    return null;
}

// ============================================================================
// EXAMPLE USAGE IN MODULE PAGES
// ============================================================================

/*
// In workout.html:
<script src="module_completion_template.js"></script>
<script>
    // When workout is complete
    document.getElementById('completeButton').addEventListener('click', () => {
        onModuleComplete('seven_minute_workout', 7, {
            exercises_completed: 12,
            difficulty: 'medium'
        });
    });
    
    // When user cancels
    document.getElementById('cancelButton').addEventListener('click', () => {
        if (confirm('Are you sure you want to cancel?')) {
            onModuleCancel();
        }
    });
    
    // Display module info
    const info = getModuleInfo();
    if (info) {
        document.getElementById('moduleTitle').textContent = info.activity_name;
    }
</script>

// In meditation.html:
<script src="module_completion_template.js"></script>
<script>
    // When meditation timer ends
    function onMeditationComplete(durationMinutes) {
        onModuleComplete('meditation_module', durationMinutes, {
            meditation_type: 'guided',
            completed_full_session: true
        });
    }
</script>

// In outdoor.html:
<script src="module_completion_template.js"></script>
<script>
    // When user marks activity as done
    document.getElementById('doneButton').addEventListener('click', () => {
        const duration = parseInt(document.getElementById('durationInput').value) || 20;
        onModuleComplete('outdoor_activity', duration, {
            activity_type: 'walk',
            location: 'park'
        });
    });
</script>
*/
