// Dashboard Configuration
const API_BASE_URL = 'http://localhost:8000/api';
const AGENT_ID = 'jenkins_agent';

// Global State
let buildsData = [];
let filteredBuilds = [];

// DOM Elements - Will be initialized after DOM loads
let refreshBtn, connectionStatus, loading, buildsContainer, emptyState;
let statusFilter, searchInput, modalOverlay, modalClose, modalTitle, modalContent;
let successRate, failureRate, totalBuilds, retryCount;
let successCount, failureCount, lastUpdate, retryRate;

// Initialize Dashboard
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM Content Loaded - Initializing dashboard...');
    
    // Initialize DOM elements with debug logging
    refreshBtn = document.getElementById('refreshBtn');
    console.log('refreshBtn:', refreshBtn);
    
    connectionStatus = document.getElementById('connectionStatus');
    console.log('connectionStatus:', connectionStatus);
    
    loading = document.getElementById('loading');
    console.log('loading:', loading);
    
    buildsContainer = document.getElementById('buildsContainer');
    console.log('buildsContainer:', buildsContainer);
    
    emptyState = document.getElementById('emptyState');
    console.log('emptyState:', emptyState);
    
    statusFilter = document.getElementById('statusFilter');
    console.log('statusFilter:', statusFilter);
    
    searchInput = document.getElementById('searchInput');
    console.log('searchInput:', searchInput);
    
    modalOverlay = document.getElementById('modalOverlay');
    console.log('modalOverlay:', modalOverlay);
    
    modalClose = document.getElementById('modalClose');
    console.log('modalClose:', modalClose);
    
    modalTitle = document.getElementById('modalTitle');
    console.log('modalTitle:', modalTitle);
    
    modalContent = document.getElementById('modalContent');
    console.log('modalContent:', modalContent);

    // Statistics Elements
    successRate = document.getElementById('successRate');
    console.log('successRate:', successRate);
    
    failureRate = document.getElementById('failureRate');
    console.log('failureRate:', failureRate);
    
    totalBuilds = document.getElementById('totalBuilds');
    console.log('totalBuilds:', totalBuilds);
    
    retryCount = document.getElementById('retryCount');
    console.log('retryCount:', retryCount);
    
    successCount = document.getElementById('successCount');
    console.log('successCount:', successCount);
    
    failureCount = document.getElementById('failureCount');
    console.log('failureCount:', failureCount);
    
    lastUpdate = document.getElementById('lastUpdate');
    console.log('lastUpdate:', lastUpdate);
    
    retryRate = document.getElementById('retryRate');
    console.log('retryRate:', retryRate);

    // Add Event Listeners only after DOM elements are found and verified
    try {
        if (refreshBtn) {
            refreshBtn.addEventListener('click', loadBuildsData);
            console.log('✅ refreshBtn event listener added');
        } else {
            console.error('❌ refreshBtn not found');
        }
        
        if (statusFilter) {
            statusFilter.addEventListener('change', filterBuilds);
            console.log('✅ statusFilter event listener added');
        } else {
            console.error('❌ statusFilter not found');
        }
        
        if (searchInput) {
            searchInput.addEventListener('input', filterBuilds);
            console.log('✅ searchInput event listener added');
        } else {
            console.error('❌ searchInput not found');
        }
        
        if (modalClose) {
            modalClose.addEventListener('click', closeModal);
            console.log('✅ modalClose event listener added');
        } else {
            console.error('❌ modalClose not found');
        }
        
        if (modalOverlay) {
            modalOverlay.addEventListener('click', (e) => {
                if (e.target === modalOverlay) closeModal();
            });
            console.log('✅ modalOverlay event listener added');
        } else {
            console.error('❌ modalOverlay not found');
        }
    } catch (error) {
        console.error('Error adding event listeners:', error);
    }

    // Load initial data
    console.log('Loading initial builds data...');
    loadBuildsData();
    
    // Auto-refresh every 30 seconds
    setInterval(loadBuildsData, 30000);
    console.log('Auto-refresh interval set to 30 seconds');
});

// Load builds data from API
async function loadBuildsData() {
    try {
        if (loading) showLoading(true);
        if (connectionStatus) updateConnectionStatus(true);
        
        const response = await fetch(`${API_BASE_URL}/agents/${AGENT_ID}/runs`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        buildsData = data || [];
        
        // Debug: log the structure of the first build
        if (buildsData.length > 0) {
            console.log('First build structure:', JSON.stringify(buildsData[0], null, 2));
        }
        
        updateStatistics();
        filterBuilds();
        updateLastUpdateTime();
        
        console.log('Loaded builds data:', buildsData.length, 'builds');
        
    } catch (error) {
        console.error('Error loading builds data:', error);
        if (connectionStatus) updateConnectionStatus(false);
        showError('Failed to load builds data. Please check your connection.');
    } finally {
        if (loading) showLoading(false);
    }
}

// Update statistics cards
function updateStatistics() {
    const total = buildsData.length;
    
    if (total === 0) {
        if (successRate) successRate.textContent = '--';
        if (failureRate) failureRate.textContent = '--';
        if (totalBuilds) totalBuilds.textContent = '0';
        if (retryCount) retryCount.textContent = '0';
        if (successCount) successCount.textContent = '0 builds';
        if (failureCount) failureCount.textContent = '0 builds';
        if (retryRate) retryRate.textContent = '0%';
        return;
    }
    
    // Count different build statuses
    const successBuilds = buildsData.filter(build => {
        const status = getBuildStatus(build);
        return status === 'SUCCESS';
    });
    
    const failureBuilds = buildsData.filter(build => {
        const status = getBuildStatus(build);
        return status === 'FAILURE';
    });
    
    const retriedBuilds = buildsData.filter(build => {
        return build.result && build.result.action_taken === 'retriggered';
    });
    
    // Calculate percentages
    const successPercentage = Math.round((successBuilds.length / total) * 100);
    const failurePercentage = Math.round((failureBuilds.length / total) * 100);
    const retryPercentage = Math.round((retriedBuilds.length / total) * 100);
    
    // Update DOM with safety checks
    if (successRate) successRate.textContent = `${successPercentage}%`;
    if (failureRate) failureRate.textContent = `${failurePercentage}%`;
    if (totalBuilds) totalBuilds.textContent = total.toString();
    if (retryCount) retryCount.textContent = retriedBuilds.length.toString();
    if (successCount) successCount.textContent = `${successBuilds.length} builds`;
    if (failureCount) failureCount.textContent = `${failureBuilds.length} builds`;
    if (retryRate) retryRate.textContent = `${retryPercentage}%`;
}

// Get build status from build data
function getBuildStatus(build) {
    // First, check if this is a running/pending build
    if (build.status) {
        const status = build.status.toUpperCase();
        if (status === 'RUNNING' || status === 'PENDING') {
            return status;
        }
        if (status === 'COMPLETED' || status === 'FINISHED') {
            // Look for the actual result
            if (build.result) {
                // Check various possible locations for the Jenkins build result
                if (build.result.webhook_data?.build?.status) {
                    return build.result.webhook_data.build.status.toUpperCase();
                }
                if (build.result.build_status) {
                    return build.result.build_status.toUpperCase();
                }
                if (build.result.result) {
                    return build.result.result.toUpperCase();
                }
            }
            return 'SUCCESS'; // Default to success if completed but no specific result
        }
        if (status === 'FAILED' || status === 'ERROR') {
            return 'FAILURE';
        }
    }
    
    // If no status, check result directly
    if (build.result) {
        if (typeof build.result === 'string') {
            return build.result.toUpperCase();
        }
        if (build.result.webhook_data?.build?.status) {
            return build.result.webhook_data.build.status.toUpperCase();
        }
        if (build.result.build_status) {
            return build.result.build_status.toUpperCase();
        }
        if (build.result.result) {
            return build.result.result.toUpperCase();
        }
    }
    
    return 'UNKNOWN';
}

// Filter and display builds
function filterBuilds() {
    if (!statusFilter || !searchInput) return;
    
    const statusFilterValue = statusFilter.value;
    const searchValue = searchInput.value.toLowerCase();
    
    filteredBuilds = buildsData.filter(build => {
        // Status filter
        let matchesStatus = true;
        if (statusFilterValue !== 'all') {
            const buildStatus = build.status ? build.status.toLowerCase() : '';
            if (statusFilterValue === 'failed') {
                const actualStatus = getBuildStatus(build);
                matchesStatus = actualStatus === 'FAILURE';
            } else {
                matchesStatus = buildStatus === statusFilterValue;
            }
        }
        
        // Search filter
        let matchesSearch = true;
        if (searchValue) {
            // Check multiple possible locations for job name and build number
            let jobName = '';
            let buildNumber = '';
            
            // Extract from input_data (webhook data)
            if (build.input_data?.input) {
                jobName = (build.input_data.input.job_name || build.input_data.input.name || '').toLowerCase();
                buildNumber = (build.input_data.input.build_number || 
                              build.input_data.input.build?.number || '').toString();
            }
            
            // Fallback to result data
            if (!jobName && build.result) {
                jobName = (build.result.job_name || '').toLowerCase();
                buildNumber = (build.result.build_number || '').toString();
            }
            
            matchesSearch = jobName.includes(searchValue) || buildNumber.includes(searchValue);
        }
        
        return matchesStatus && matchesSearch;
    });
    
    displayBuilds();
}

// Display builds in the container
function displayBuilds() {
    if (!buildsContainer || !emptyState) return;
    
    if (filteredBuilds.length === 0) {
        buildsContainer.style.display = 'none';
        emptyState.style.display = 'block';
        return;
    }
    
    buildsContainer.style.display = 'block';
    emptyState.style.display = 'none';
    
    // Sort builds by started_at (newest first)
    const sortedBuilds = [...filteredBuilds].sort((a, b) => 
        new Date(b.started_at) - new Date(a.started_at)
    );
    
    buildsContainer.innerHTML = sortedBuilds.map(build => createBuildHTML(build)).join('');
    
    // Add click listeners to build items
    document.querySelectorAll('.build-item').forEach((item, index) => {
        item.addEventListener('click', () => showBuildDetails(sortedBuilds[index]));
    });
}

// Create HTML for a single build item
function createBuildHTML(build) {
    const status = getBuildStatus(build);
    
    // Extract job information from multiple possible sources
    let jobName = 'Unknown Job';
    let buildNumber = 'N/A';
    
    // Check input_data first (webhook data)
    if (build.input_data?.input) {
        jobName = build.input_data.input.job_name || build.input_data.input.name || jobName;
        buildNumber = build.input_data.input.build_number || 
                     build.input_data.input.build?.number || buildNumber;
    }
    
    // Fallback to result data
    if (jobName === 'Unknown Job' && build.result) {
        jobName = build.result.job_name || build.result.webhook_data?.name || jobName;
    }
    if (buildNumber === 'N/A' && build.result) {
        buildNumber = build.result.build_number || 
                     build.result.webhook_data?.build?.number || buildNumber;
    }
    
    // Fallback to run_id parsing
    if (jobName === 'Unknown Job' && build.run_id) {
        const parts = build.run_id.split('-');
        if (parts.length > 1) {
            jobName = parts.slice(0, -1).join('-');
            buildNumber = parts[parts.length - 1];
        }
    }
    
    const startTime = formatDateTime(build.started_at);
    const duration = calculateDuration(build.started_at, build.completed_at);
    
    // Extract action taken
    let actionTaken = 'none';
    if (build.result?.action_taken) {
        actionTaken = build.result.action_taken;
    } else if (build.status === 'completed' && status !== 'UNKNOWN') {
        actionTaken = 'analyzed';
    }
    
    // Get AI analysis summary
    let analysisText = 'No analysis available';
    if (build.result?.failure_analysis?.cause) {
        analysisText = build.result.failure_analysis.cause;
    } else if (build.result?.success_analysis?.summary) {
        analysisText = build.result.success_analysis.summary;
    } else if (build.result?.analysis) {
        analysisText = typeof build.result.analysis === 'string' ? 
                      build.result.analysis : 
                      JSON.stringify(build.result.analysis);
    } else if (build.logs && build.logs.length > 0) {
        analysisText = build.logs[build.logs.length - 1] || 'Processing...';
    }
    
    const statusClass = status === 'SUCCESS' ? 'success' : 
                       status === 'FAILURE' ? 'failure' : 
                       status === 'RUNNING' ? 'running' : 'completed';
    
    const actionClass = actionTaken === 'retriggered' ? 'retriggered' : 'notified';
    
    return `
        <div class="build-item" data-run-id="${build.run_id}">
            <div class="build-header">
                <div class="build-info">
                    <span class="build-status ${statusClass}">${status}</span>
                    <span class="build-title">${jobName}</span>
                    <span class="build-number">#${buildNumber}</span>
                </div>
                <div class="build-time">${startTime}</div>
            </div>
            
            <div class="build-details">
                <div class="detail-item">
                    <span class="detail-label">Duration</span>
                    <span class="detail-value">${duration}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Status</span>
                    <span class="detail-value">${build.status}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Action Taken</span>
                    <span class="detail-value">
                        ${actionTaken !== 'none' ? 
                            `<span class="action-taken ${actionClass}">${actionTaken}</span>` : 
                            'None'
                        }
                    </span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">AI Analysis</span>
                    <span class="detail-value">${truncateText(analysisText, 100)}</span>
                </div>
            </div>
        </div>
    `;
}

// Show detailed build information in modal
function showBuildDetails(build) {
    const status = getBuildStatus(build);
    const jobName = build.result?.job_name || 'Unknown Job';
    const buildNumber = build.result?.build_number || 'N/A';
    
    modalTitle.textContent = `${jobName} #${buildNumber} - ${status}`;
    
    modalContent.innerHTML = `
        <div class="modal-section">
            <h4><i class="fas fa-info-circle"></i> Build Information</h4>
            <div class="info-grid">
                <div class="info-item">
                    <span class="info-label">Job Name</span>
                    <span class="info-value">${jobName}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Build Number</span>
                    <span class="info-value">#${buildNumber}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Status</span>
                    <span class="info-value">${status}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Agent Status</span>
                    <span class="info-value">${build.status}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Started At</span>
                    <span class="info-value">${formatDateTime(build.started_at)}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Completed At</span>
                    <span class="info-value">${build.completed_at ? formatDateTime(build.completed_at) : 'N/A'}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Duration</span>
                    <span class="info-value">${calculateDuration(build.started_at, build.completed_at)}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Action Taken</span>
                    <span class="info-value">${build.result?.action_taken || 'None'}</span>
                </div>
            </div>
        </div>
        
        ${createAIAnalysisSection(build)}
        ${createJenkinsLogsSection(build)}
        ${createJenkinsfileSection(build)}
        ${createActionLogsSection(build)}
    `;
    
    modalOverlay.classList.add('active');
}

// Create AI Analysis section
function createAIAnalysisSection(build) {
    const result = build.result;
    if (!result) return '';
    
    let analysisHTML = '';
    
    // Failure Analysis
    if (result.failure_analysis) {
        const analysis = result.failure_analysis;
        analysisHTML = `
            <div class="modal-section">
                <h4><i class="fas fa-brain"></i> AI Failure Analysis</h4>
                <div class="info-grid">
                    <div class="info-item">
                        <span class="info-label">Root Cause</span>
                        <span class="info-value">${analysis.cause || 'Unknown'}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Category</span>
                        <span class="info-value">${analysis.category || 'Unknown'}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Confidence</span>
                        <span class="info-value">${Math.round((analysis.confidence || 0) * 100)}%</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Decision</span>
                        <span class="info-value">${result.decision || 'N/A'}</span>
                    </div>
                </div>
                ${analysis.suggested_actions && analysis.suggested_actions.length > 0 ? `
                    <h5 style="margin: 20px 0 10px 0; color: #4a5568;">Suggested Actions</h5>
                    <ul class="suggestions-list">
                        ${analysis.suggested_actions.map(action => `<li>${action}</li>`).join('')}
                    </ul>
                ` : ''}
            </div>
        `;
    }
    
    // Success Analysis
    if (result.success_analysis) {
        const analysis = result.success_analysis;
        analysisHTML = `
            <div class="modal-section">
                <h4><i class="fas fa-lightbulb"></i> AI Success Analysis</h4>
                <div class="info-grid">
                    <div class="info-item">
                        <span class="info-label">Summary</span>
                        <span class="info-value">${analysis.summary || 'No summary available'}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Confidence</span>
                        <span class="info-value">${Math.round((analysis.confidence || 0) * 100)}%</span>
                    </div>
                </div>
                ${analysis.improvements && analysis.improvements.length > 0 ? `
                    <h5 style="margin: 20px 0 10px 0; color: #4a5568;">Suggested Improvements</h5>
                    <ul class="suggestions-list">
                        ${analysis.improvements.map(improvement => `<li>${improvement}</li>`).join('')}
                    </ul>
                ` : ''}
            </div>
        `;
    }
    
    return analysisHTML;
}

// Create Jenkins Logs section
function createJenkinsLogsSection(build) {
    const logs = build.result?.jenkins_logs;
    if (!logs) return '';
    
    return `
        <div class="modal-section">
            <h4><i class="fas fa-terminal"></i> Jenkins Console Logs</h4>
            <div class="code-block">${escapeHtml(logs)}</div>
        </div>
    `;
}

// Create Jenkinsfile section
function createJenkinsfileSection(build) {
    const jenkinsfile = build.result?.jenkinsfile_content;
    if (!jenkinsfile) return '';
    
    return `
        <div class="modal-section">
            <h4><i class="fas fa-file-code"></i> Jenkinsfile</h4>
            <div class="code-block">${escapeHtml(jenkinsfile)}</div>
        </div>
    `;
}

// Create Action Logs section
function createActionLogsSection(build) {
    if (!build.logs || build.logs.length === 0) return '';
    
    return `
        <div class="modal-section">
            <h4><i class="fas fa-list-alt"></i> Agent Execution Logs</h4>
            <div class="code-block">${build.logs.map(log => escapeHtml(log)).join('\n')}</div>
        </div>
    `;
}

// Close modal
function closeModal() {
    modalOverlay.classList.remove('active');
}

// Utility Functions
function formatDateTime(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString();
}

function calculateDuration(startTime, endTime) {
    if (!startTime) return 'N/A';
    if (!endTime) return 'Running...';
    
    const start = new Date(startTime);
    const end = new Date(endTime);
    const durationMs = end - start;
    
    const seconds = Math.floor(durationMs / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    
    if (minutes > 0) {
        return `${minutes}m ${remainingSeconds}s`;
    } else {
        return `${remainingSeconds}s`;
    }
}

function truncateText(text, maxLength) {
    if (!text || text.length <= maxLength) return text || '';
    return text.substring(0, maxLength) + '...';
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showLoading(show) {
    if (loading) loading.style.display = show ? 'flex' : 'none';
}

function updateConnectionStatus(connected) {
    if (!connectionStatus) return;
    
    const statusEl = connectionStatus;
    const icon = statusEl.querySelector('i');
    const text = statusEl.querySelector('span') || statusEl;
    
    if (connected) {
        statusEl.style.color = '#48bb78';
        if (icon) icon.className = 'fas fa-circle';
        if (text !== statusEl) text.textContent = 'Connected';
        else statusEl.innerHTML = '<i class="fas fa-circle"></i> Connected';
    } else {
        statusEl.style.color = '#f56565';
        if (icon) icon.className = 'fas fa-exclamation-circle';
        if (text !== statusEl) text.textContent = 'Disconnected';
        else statusEl.innerHTML = '<i class="fas fa-exclamation-circle"></i> Disconnected';
    }
}

function updateLastUpdateTime() {
    if (lastUpdate) lastUpdate.textContent = `Updated: ${new Date().toLocaleTimeString()}`;
}

function showError(message) {
    console.error(message);
    // You could implement a toast notification here
    // For now, just log to console
}
