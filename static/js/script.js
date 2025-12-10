document.addEventListener('DOMContentLoaded', () => {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const browseButton = document.getElementById('browseButton');
    const fileNameDisplay = document.getElementById('fileName');
    const colorizeBtn = document.getElementById('colorizeBtn');
    const bwBtn = document.getElementById('bwBtn');
    const outputArea = document.getElementById('outputArea');
    
    // Log & Progress Elements
    const logContainer = document.getElementById('logContainer');
    const logText = document.getElementById('logText');
    const progressBarContainer = document.getElementById('progressBarContainer');
    const progressBar = document.getElementById('progressBar');

    let currentFile = null;
    let pollInterval = null;

    // --- File Input Logic ---
    browseButton.addEventListener('click', (e) => { e.stopPropagation(); fileInput.click(); });
    uploadArea.addEventListener('click', () => fileInput.click());
    
    fileInput.addEventListener('change', handleFileSelect);
    
    uploadArea.addEventListener('dragover', (e) => { e.preventDefault(); uploadArea.classList.add('dragover'); });
    uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('dragover'));
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault(); uploadArea.classList.remove('dragover');
        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            handleFileSelect({ target: fileInput });
        }
    });

    function handleFileSelect(event) {
        currentFile = event.target.files[0];
        if (currentFile) {
            fileNameDisplay.textContent = currentFile.name;
            colorizeBtn.disabled = false;
            bwBtn.disabled = false;
            outputArea.innerHTML = '';
            logContainer.style.display = 'none';
        }
    }

    // --- Processing Logic ---
    colorizeBtn.addEventListener('click', () => startProcessing('colorize'));
    bwBtn.addEventListener('click', () => startProcessing('bw'));

    function startProcessing(mode) {
        if (!currentFile) return;

        // UI Reset
        colorizeBtn.disabled = true;
        bwBtn.disabled = true;
        outputArea.innerHTML = '';
        logContainer.style.display = 'flex';
        logText.textContent = `Initializing ${mode} process for ${currentFile.name}...`;
        progressBarContainer.style.display = 'block';
        progressBar.style.width = '0%';

        const formData = new FormData();
        formData.append('file', currentFile);
        formData.append('mode', mode);

        // 1. Send File to start processing
        fetch('/process', { method: 'POST', body: formData })
        .then(response => response.json())
        .then(data => {
            if (data.error) throw new Error(data.error);
            // 2. Start Polling for status using the Task ID
            pollStatus(data.task_id);
        })
        .catch(err => {
            logText.textContent = `Error: ${err.message}`;
            logText.style.color = '#ff6b6b';
            enableButtons();
        });
    }

    function pollStatus(taskId) {
        pollInterval = setInterval(() => {
            fetch(`/status/${taskId}`)
            .then(res => res.json())
            .then(data => {
                // Update Log Text
                if (data.log) logText.textContent = data.log;
                
                // Update Progress Bar (if available)
                if (data.progress) progressBar.style.width = `${data.progress}%`;

                if (data.status === 'completed') {
                    clearInterval(pollInterval);
                    progressBar.style.width = '100%';
                    logText.textContent = "Processing complete! Loading result...";
                    setTimeout(() => {
                        displayOutput(data.result.url, data.result.is_video, data.result.filename);
                        enableButtons();
                    }, 1000);
                } 
                else if (data.status === 'error') {
                    clearInterval(pollInterval);
                    logText.style.color = '#ff6b6b';
                    enableButtons();
                }
            })
            .catch(err => {
                console.error(err);
                clearInterval(pollInterval);
            });
        }, 1000); // Check every 1 second
    }

    function displayOutput(url, isVideo, filename) {
        const timestampedUrl = `${url}?t=${new Date().getTime()}`;
        outputArea.innerHTML = '';
        
        // Create Container
        const container = document.createElement('div');
        container.style.display = "flex";
        container.style.flexDirection = "column";
        container.style.alignItems = "center";

        if (isVideo) {
            const video = document.createElement('video');
            video.controls = true;
            video.autoplay = true;
            video.muted = true; // Required for autoplay
            video.loop = true;
            video.style.maxWidth = "100%";
            video.style.borderRadius = "10px";
            video.style.border = "1px solid rgba(255,255,255,0.2)";
            
            // Source with cache busting
            video.src = timestampedUrl;

            // Handle Playback Errors (Codec issues)
            video.onerror = () => {
                video.style.display = 'none';
                const errorMsg = document.createElement('p');
                errorMsg.style.color = '#ff6b6b';
                errorMsg.style.marginTop = '15px';
                errorMsg.innerHTML = `⚠️ <strong>Preview Unavailable:</strong> The video format isn't supported by your browser.<br>Please use the <strong>Download</strong> button below to view it.`;
                container.insertBefore(errorMsg, container.firstChild);
            };

            container.appendChild(video);
        } else {
            const img = document.createElement('img');
            img.src = timestampedUrl;
            img.style.maxWidth = "100%";
            img.style.borderRadius = "10px";
            img.style.boxShadow = "0 10px 30px rgba(0,0,0,0.5)";
            container.appendChild(img);
        }

        // Distinct Download Button
        const dlBtn = document.createElement('a');
        dlBtn.href = url;
        dlBtn.download = filename || 'processed_result';
        dlBtn.className = "btn"; // Re-use the main button style
        dlBtn.style.marginTop = "20px";
        dlBtn.style.background = "#2ecc71"; // Green for success
        dlBtn.style.border = "none";
        dlBtn.innerHTML = `<span class="material-symbols-outlined">download</span> Download Result`;
        
        container.appendChild(dlBtn);
        outputArea.appendChild(container);
    }

    function enableButtons() {
        colorizeBtn.disabled = false;
        bwBtn.disabled = false;
        // Don't hide log container immediately so user can see what happened
    }
});
