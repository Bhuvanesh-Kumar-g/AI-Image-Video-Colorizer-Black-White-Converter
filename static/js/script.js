// D:\PROJECT\ML b&w colorizer Project\static\js\script.js
document.addEventListener('DOMContentLoaded', () => {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const browseButton = document.getElementById('browseButton');
    const fileNameDisplay = document.getElementById('fileName');
    const colorizeBtn = document.getElementById('colorizeBtn');
    const bwBtn = document.getElementById('bwBtn');
    const statusText = document.getElementById('statusText');
    const outputArea = document.getElementById('outputArea');
    const progressBarContainer = document.getElementById('progressBarContainer');
    const progressBar = document.getElementById('progressBar');

    // **MODIFIED: Theme Toggle Elements**
    const themeToggleBtn = document.getElementById('themeToggleBtn');
    const themeIcon = document.getElementById('themeIcon');
    const bodyElement = document.body;

    let currentFile = null;

    // --- File Selection ---
    browseButton.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileSelect);

    // --- Drag and Drop ---
    uploadArea.addEventListener('dragover', (event) => {
        event.preventDefault();
        uploadArea.classList.add('dragover');
    });
    uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('dragover'));
    uploadArea.addEventListener('drop', (event) => {
        event.preventDefault();
        uploadArea.classList.remove('dragover');
        if (event.dataTransfer.files && event.dataTransfer.files.length > 0) {
            fileInput.files = event.dataTransfer.files;
            handleFileSelect({ target: fileInput });
        }
    });
    uploadArea.addEventListener('click', (event) => {
        if (event.target !== browseButton && !browseButton.contains(event.target)) {
            fileInput.click();
        }
    });

    function handleFileSelect(event) {
        currentFile = event.target.files[0];
        if (currentFile) {
            fileNameDisplay.textContent = currentFile.name;
            colorizeBtn.disabled = false;
            bwBtn.disabled = false;
            outputArea.innerHTML = '';
            updateStatus('File selected: ' + currentFile.name, 'info');
        } else {
            fileNameDisplay.textContent = '';
            colorizeBtn.disabled = true;
            bwBtn.disabled = true;
            updateStatus('Select a file to begin.', 'info');
        }
    }

    // --- Button Clicks ---
    colorizeBtn.addEventListener('click', () => processFile('colorize'));
    bwBtn.addEventListener('click', () => processFile('bw'));

    function processFile(mode) {
        if (!currentFile) {
            updateStatus('Please select a file first.', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('file', currentFile);
        formData.append('mode', mode);

        updateStatus(`Processing ${currentFile.name} (${mode})... This may take a while.`, 'processing');
        colorizeBtn.disabled = true;
        bwBtn.disabled = true;
        outputArea.innerHTML = '';
        progressBar.style.width = '0%';
        progressBarContainer.style.display = 'block';

        let progress = 0;
        const interval = setInterval(() => {
            progress += 5;
            progressBar.style.width = Math.min(progress, 95) + '%';
            if (progress >= 95) clearInterval(interval);
        }, 200);

        fetch('/process', { method: 'POST', body: formData })
        .then(response => {
            clearInterval(interval);
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.error || `Server error: ${response.status}`) });
            }
            return response.json();
        })
        .then(data => {
            progressBar.style.width = '100%';
            setTimeout(() => { progressBarContainer.style.display = 'none'; }, 500);
            if (data.error) {
                updateStatus(`Error: ${data.error}`, 'error');
            } else {
                updateStatus(data.message || 'Processing complete!', 'success');
                displayOutput(data.processed_file_url, data.is_video, data.filename); // Pass filename for download link
            }
        })
        .catch(error => {
            clearInterval(interval);
            progressBarContainer.style.display = 'none';
            console.error('Processing error:', error);
            updateStatus(`Client-side or network error: ${error.message}`, 'error');
        })
        .finally(() => {
            if (currentFile) {
                 colorizeBtn.disabled = false;
                 bwBtn.disabled = false;
            }
        });
    }

    function updateStatus(message, type = 'info') {
        statusText.textContent = message;
        statusText.className = '';
        if (type) statusText.classList.add(type);
    }

    // **MODIFIED: displayOutput for better video handling**
    function displayOutput(fileUrl, isVideo, filename) {
        outputArea.innerHTML = ''; // Clear previous
        let mediaElement;

        if (isVideo) {
            mediaElement = document.createElement('video');
            mediaElement.controls = true;
            mediaElement.autoplay = true;
            mediaElement.muted = true;   // Essential for autoplay in most browsers
            mediaElement.loop = true;
            mediaElement.style.maxWidth = '100%';
            mediaElement.style.maxHeight = '500px'; // Adjust if needed
            
            // Add event listener for errors loading the video
            mediaElement.addEventListener('error', function(e) {
                console.error('Error loading video:', e);
                console.error('Video src was:', mediaElement.src);
                let errorMsg = 'Could not load video. The file might be corrupted or in an unsupported format.';
                if (e.target && e.target.error) {
                    switch (e.target.error.code) {
                        case e.target.error.MEDIA_ERR_ABORTED: errorMsg = 'Video playback aborted.'; break;
                        case e.target.error.MEDIA_ERR_NETWORK: errorMsg = 'A network error caused video download to fail.'; break;
                        case e.target.error.MEDIA_ERR_DECODE: errorMsg = 'Video decoding error. File may be corrupted or unsupported.'; break;
                        case e.target.error.MEDIA_ERR_SRC_NOT_SUPPORTED: errorMsg = 'Video source not supported. Check the URL or format.'; break;
                        default: errorMsg = 'An unknown error occurred while loading the video.';
                    }
                }
                outputArea.innerHTML = `<p style="color: var(--error-color);">${errorMsg}</p>
                                        <p>Try downloading it: <a href="${fileUrl}" download="${filename || 'video.mp4'}" target="_blank">${filename || 'Download Video'}</a></p>`;
            });

            // Add event listener for when video can play
            mediaElement.addEventListener('canplay', function() {
                console.log('Video can play. Source:', mediaElement.src);
            });
            
        } else {
            mediaElement = document.createElement('img');
            mediaElement.style.maxWidth = '100%';
            mediaElement.style.maxHeight = '500px'; // Adjust if needed
             mediaElement.alt = filename || "Processed Image";
        }
        
        // IMPORTANT: Ensure the URL is correctly formed and the server serves it
        // Adding a timestamp can help bust caches during development
        // const cacheBusterUrl = fileUrl + '?t=' + new Date().getTime();
        // mediaElement.src = cacheBusterUrl; 
        mediaElement.src = fileUrl; // Use direct URL first

        outputArea.appendChild(mediaElement);

        if (isVideo) {
            mediaElement.load(); // Explicitly call load for video after src is set
            // mediaElement.play().catch(error => console.warn("Autoplay prevented:", error)); // Attempt to play if autoplay is set
        }
    }

    // **MODIFIED: Theme Toggle Logic**
    function applyTheme(theme) {
        if (theme === 'dark') {
            bodyElement.classList.add('dark-mode');
            themeIcon.textContent = 'brightness_4'; // Moon icon
        } else {
            bodyElement.classList.remove('dark-mode');
            themeIcon.textContent = 'brightness_7'; // Sun icon
        }
    }

    // Load saved theme preference or default to system preference
    let currentTheme = localStorage.getItem('theme');
    if (!currentTheme) {
        currentTheme = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    applyTheme(currentTheme);

    themeToggleBtn.addEventListener('click', () => {
        let newTheme = bodyElement.classList.contains('dark-mode') ? 'light' : 'dark';
        applyTheme(newTheme);
        localStorage.setItem('theme', newTheme);
    });

    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        const newColorScheme = e.matches ? "dark" : "light";
        // Only change if no explicit user preference is set
        if (!localStorage.getItem('theme')) {
            applyTheme(newColorScheme);
        }
    });
});