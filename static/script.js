// Default user ID - you can modify this or make it dynamic
const DEFAULT_USER_ID = 'web_user';

// Moods that require reason collection
const NEGATIVE_MOODS = ['horrible', 'not good', 'tired'];

// Function to log mood when emoji is clicked
async function logMood(moodValue) {
    // Check if this mood requires reason collection
    if (NEGATIVE_MOODS.includes(moodValue.toLowerCase())) {
        showReasonModal(moodValue);
    } else {
        // Direct mood logging for positive moods
        await submitMood(moodValue);
    }
}

// Function to show reason collection modal
function showReasonModal(moodValue) {
    const modal = document.getElementById('reasonModal');
    const moodTitle = document.getElementById('modalMoodTitle');
    
    moodTitle.textContent = `You're feeling ${moodValue}`;
    modal.style.display = 'block';
    
    // Store the mood value for later submission
    modal.dataset.mood = moodValue;
}

// Function to close the reason modal
function closeReasonModal() {
    const modal = document.getElementById('reasonModal');
    modal.style.display = 'none';
    
    // Clear the form
    document.getElementById('reasonForm').reset();
}

// Function to submit mood with reason
async function submitMoodWithReason() {
    const modal = document.getElementById('reasonModal');
    const moodValue = modal.dataset.mood;
    const reason = document.getElementById('reasonSelect').value;
    
    if (!reason) {
        showMessage('Please select a reason', 'error');
        return;
    }
    
    await submitMood(moodValue, reason);
    closeReasonModal();
}

// Main function to submit mood to API
async function submitMood(moodValue, reason = null) {
    try {
        // Show loading state
        showMessage('Logging your mood...', 'info');
        
        // Log the API call for debugging
        console.log(`Making API call to /api/mood with mood: ${moodValue}${reason ? `, reason: ${reason}` : ''}`);
        
        const requestBody = {
            user_id: DEFAULT_USER_ID,
            mood: moodValue
        };
        
        if (reason) {
            requestBody.reason = reason;
        }
        
        const response = await fetch('/api/mood', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody)
        });

        const data = await response.json();
        
        // Log the response for debugging
        console.log('API Response:', data);
        
        // Show debug info if enabled
        showDebugInfo(data);

        if (response.ok) {
            // Show success message
            showMessage(data.message, 'success');
            
            // Only show suggestions and videos for negative moods
            if (NEGATIVE_MOODS.includes(moodValue.toLowerCase())) {
                // Show suggestion if available
                if (data.suggestion) {
                    showSuggestion(data.suggestion);
                } else {
                    hideSuggestion();
                }
                
                // Show video recommendations if available
                if (data.videos && data.videos.length > 0) {
                    showVideoRecommendations(data.videos);
                } else {
                    hideVideoRecommendations();
                }
            } else {
                // Hide suggestions and videos for positive moods
                hideSuggestion();
                hideVideoRecommendations();
            }
            
            // Add visual feedback to clicked mood
            highlightMoodSelection(moodValue);
            
        } else {
            // Show error message
            showMessage(data.error || 'Failed to log mood', 'error');
        }

    } catch (error) {
        console.error('Error logging mood:', error);
        showMessage('Network error. Please try again.', 'error');
    }
}

// Function to show messages
function showMessage(text, type = 'info') {
    const messageDiv = document.getElementById('message');
    messageDiv.textContent = text;
    messageDiv.className = `message ${type}`;
    messageDiv.style.display = 'block';
    
    // Auto-hide success messages after 3 seconds
    if (type === 'success') {
        setTimeout(() => {
            messageDiv.style.display = 'none';
        }, 3000);
    }
}

// Function to show suggestions
function showSuggestion(suggestion) {
    const suggestionDiv = document.getElementById('suggestion');
    
    // Handle both string and object formats
    let suggestionText;
    let sourceInfo = '';
    
    if (typeof suggestion === 'string') {
        suggestionText = suggestion;
        sourceInfo = 'rule_based_fallback';
    } else if (suggestion && suggestion.text) {
        suggestionText = suggestion.text;
        sourceInfo = suggestion.source || 'unknown';
        
        // Enhanced logging with more details
        console.log(`🤖 Suggestion Details:`, {
            source: suggestion.source,
            category: suggestion.category,
            text: suggestion.text.substring(0, 50) + '...'
        });
        
        // Show user-friendly message about the source
        if (suggestion.source === 'llm_enhanced') {
            console.log(`✨ AI-Enhanced Suggestion: Selected "${suggestion.category}" based on your context`);
        } else if (suggestion.source === 'rule_based_fallback') {
            console.log(`🔧 Fallback Suggestion: Using rule-based system`);
        }
    } else {
        console.error('Invalid suggestion format:', suggestion);
        return;
    }
    
    // Add source indicator to the suggestion text
    let sourceEmoji, sourceLabel;
    
    if (sourceInfo === 'openai_llm') {
        sourceEmoji = '🤖';
        sourceLabel = 'OpenAI GPT';
    } else if (sourceInfo === 'smart_rules') {
        sourceEmoji = '🧠';
        sourceLabel = 'Smart Rules';
    } else {
        sourceEmoji = '🔧';
        sourceLabel = 'Rule-Based';
    }
    
    // Create enhanced suggestion display
    suggestionDiv.innerHTML = `
        <div class="suggestion-content">
            <div class="suggestion-text">${suggestionText}</div>
            <div class="suggestion-source" title="Suggestion source: ${sourceLabel}">
                ${sourceEmoji} ${sourceLabel}
            </div>
        </div>
    `;
    suggestionDiv.style.display = 'block';
}

// Function to show video recommendations
function showVideoRecommendations(videos) {
    const videoDiv = document.getElementById('videoRecommendations');
    
    if (!videos || videos.length === 0) {
        videoDiv.style.display = 'none';
        return;
    }
    
    let videoHTML = '<h3>🎵 Recommended for you:</h3><div class="video-grid">';
    
    videos.forEach(video => {
        videoHTML += `
            <div class="video-item">
                <a href="${video.url}" target="_blank" class="video-link">
                    <div class="video-title">${video.title}</div>
                    <div class="video-type">${video.type}</div>
                </a>
            </div>
        `;
    });
    
    videoHTML += '</div>';
    videoDiv.innerHTML = videoHTML;
    videoDiv.style.display = 'block';
}

// Function to hide suggestions
function hideSuggestion() {
    const suggestionDiv = document.getElementById('suggestion');
    suggestionDiv.style.display = 'none';
}

// Function to hide video recommendations
function hideVideoRecommendations() {
    const videoDiv = document.getElementById('videoRecommendations');
    videoDiv.style.display = 'none';
}

// Function to highlight selected mood
function highlightMoodSelection(moodValue) {
    // Remove previous highlights
    document.querySelectorAll('.mood-item').forEach(item => {
        item.style.border = '2px solid transparent';
    });
    
    // Find and highlight the selected mood
    const moodItems = document.querySelectorAll('.mood-item');
    moodItems.forEach(item => {
        const label = item.querySelector('.mood-label').textContent.toLowerCase();
        if (label === moodValue.toLowerCase()) {
            item.style.border = '2px solid #28a745';
            item.style.background = '#e8f5e8';
            
            // Reset highlight after 2 seconds
            setTimeout(() => {
                item.style.border = '2px solid transparent';
                item.style.background = '#f8f9fa';
            }, 2000);
        }
    });
}

// Add some interactive feedback
document.addEventListener('DOMContentLoaded', function() {
    // Add hover effects and click animations
    const moodItems = document.querySelectorAll('.mood-item');
    
    moodItems.forEach(item => {
        item.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px) scale(1.02)';
        });
        
        item.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
});

// Debug functionality
function showDebugInfo(data) {
    // Only show if debug mode is enabled (you can toggle this)
    const debugMode = localStorage.getItem('moodDebugMode') === 'true';
    
    if (debugMode && data.suggestion) {
        const suggestion = data.suggestion;
        if (typeof suggestion === 'object' && suggestion.source) {
            showMessage(`Debug: ${suggestion.source} | Category: ${suggestion.category}`, 'info');
        }
    }
}

// Toggle debug mode (call this in browser console)
function toggleDebugMode() {
    const current = localStorage.getItem('moodDebugMode') === 'true';
    localStorage.setItem('moodDebugMode', (!current).toString());
    console.log(`Debug mode ${!current ? 'enabled' : 'disabled'}`);
    return !current;
}