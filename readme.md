# AI Image & Video Colorizer / B&W Converter

This project provides a web application to automatically colorize black and white images and videos, or convert color media to black and white, using a deep learning model.



## Features

*   **Image Colorization:** Upload a black and white image to get a colorized version.
*   **Video Colorization:** Upload a black and white video to get a colorized version (processed frame by frame).
*   **B&W Conversion:** Convert color images or videos to black and white.
*   **Web Interface:** User-friendly web UI with drag-and-drop file support.
*   **Dark/Light Mode:** Toggle between dark and light themes for comfortable viewing.
*   **OpenCV DNN Model:** Utilizes a pre-trained Caffe model for colorization.

## Project Structure
Use code with caution.
Markdown
.
├── app.py # Flask backend application
├── models/ # Pre-trained Caffe model files
│ ├── colorization_deploy_v2.prototxt
│ ├── colorization_release_v2.caffemodel
│ └── pts_in_hull.npy
├── static/ # Frontend static assets
│ ├── css/
│ │ └── style.css
│ └── js/
│ └── script.js
├── templates/ # HTML templates
│ └── index.html
├── uploads/ # Temporary directory for uploaded files (auto-created)
├── processed_files/ # Directory for processed output files (auto-created)
├── README.md # This file
└── requirements.txt # Python dependencies (generate this file)
## Prerequisites

*   Python 3.7+
*   `pip` (Python package installer)

## Setup and Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git
    cd YOUR_REPOSITORY_NAME
    ```

2.  **Create and Activate a Virtual Environment (Recommended):**
    *   **Windows:**
        ```bash
        python -m venv venv
        .\venv\Scripts\activate
        ```
    *   **macOS/Linux:**
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```

3.  **Install Dependencies:**
    Make sure you have a `requirements.txt` file in your project root with the following content:
    ```txt
    Flask==2.3.3 
    Werkzeug==2.3.7 
    numpy==1.24.4
    opencv-python==4.8.0.76
    # Add other specific versions if you know them
    # Or use 'pip freeze > requirements.txt' after installing manually
    ```
    Then run:
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: It's good practice to pin dependency versions. You can generate this file by running `pip freeze > requirements.txt` after manually installing the packages below if you prefer.)*

    Alternatively, install packages manually:
    ```bash
    pip install Flask numpy opencv-python
    ```

4.  **Download Model Files:**
    The colorization model consists of three files:
    *   `colorization_deploy_v2.prototxt`
    *   `colorization_release_v2.caffemodel`
    *   `pts_in_hull.npy`

    Place these files into the `models/` directory. You can typically find these files from the original source of the colorization model (e.g., [Zhang et al., 2016 - Colorful Image Colorization](https://richzhang.github.io/colorization/)).
    *   **Direct Links (if available and permitted by license):**
        *   Prototxt: [Link to prototxt file]
        *   Caffemodel: [Link to caffemodel file]
        *   pts_in_hull.npy: [Link to npy file]
    *(Important: Verify the source and license of these model files. If you cannot provide direct links, guide users on how to obtain them, e.g., "Download from the official project page linked in References.")*

    **Ensure the `models/` directory exists and contains these files before running the application.**

## Running the Application

1.  Navigate to the project's root directory (e.g., `YOUR_REPOSITORY_NAME`).
2.  Run the Flask application:
    ```bash
    python app.py
    ```
3.  Open your web browser and go to: `http://127.0.0.1:5000/`

    If you started the app with `host='0.0.0.0'`, you can also access it from other devices on your local network using your machine's IP address (e.g., `http://YOUR_MACHINE_IP:5000/`).

## Usage

1.  **Upload File:** Drag and drop an image or video file onto the designated area, or click "browse" to select a file.
    *   Supported image formats: `.png`, `.jpg`, `.jpeg`
    *   Supported video formats: `.mp4`, `.avi`, `.mov`, `.mkv` (output will always be `.mp4`)
2.  **Choose Action:**
    *   Click "🎨 Colorize" to colorize the uploaded media.
    *   Click "⚫ Convert to B&W" to convert the media to black and white.
3.  **Processing:** A status message and progress bar will indicate that processing is underway. This can take some time, especially for videos.
4.  **View Output:** The processed image or video will be displayed on the page.
5.  **Theme Toggle:** Click the sun/moon icon in the top-right corner to switch between light and dark modes.

## Technical Details

*   **Backend:** Flask (Python)
*   **Frontend:** HTML, CSS, JavaScript (vanilla)
*   **Colorization Model:** Caffe deep learning model via OpenCV's DNN module.
    *   Based on the work by Zhang et al. (2016).
*   **Image/Video Processing:** OpenCV

## Troubleshooting

*   **Model Files Not Found:** Ensure the `models/` directory exists and contains `colorization_deploy_v2.prototxt`, `colorization_release_v2.caffemodel`, and `pts_in_hull.npy`.
*   **Video Not Playing:**
    *   Try clearing your browser cache for the site.
    *   Check the browser's developer console (usually F12) for errors related to media playback or network requests.
    *   The output video format is MP4 (`mp4v` codec). Ensure your browser supports this.
*   **Large File Uploads:** The application has a default upload limit (currently 200MB). For larger files, you might need to adjust `app.config['MAX_CONTENT_LENGTH']` in `app.py` and potentially configure your web server (if deploying to production) to handle larger request bodies.
*   **"Address already in use" Error:** Port 5000 is already being used by another application. You can either stop the other application or change the port in `app.py` (e.g., `app.run(host='0.0.0.0', port=5001, debug=True)`).

## Future Enhancements

*   Real-time processing progress updates from backend to frontend (e.g., using WebSockets or Server-Sent Events).
*   Option to adjust processing parameters.
*   Support for more file formats.
*   More advanced UI/UX for error handling and feedback.
*   Batch processing.
*   User accounts and history.
*   Deployment instructions for production environments (e.g., using Gunicorn, Nginx, Docker).

## References

*   Zhang, R., Isola, P., & Efros, A. A. (2016). Colorful Image Colorization. In *European Conference on Computer Vision (ECCV)*.
    *   Project Page: [https://richzhang.github.io/colorization/](https://richzhang.github.io/colorization/)
    *   Paper: [https://arxiv.org/abs/1603.08511](https://arxiv.org/abs/1603.08511)
*   OpenCV (Open Source Computer Vision Library): [https://opencv.org/](https://opencv.org/)
*   Flask Web Framework: [https://flask.palletsprojects.com/](https://flask.palletsprojects.com/)
*   Material Icons: [https://fonts.google.com/icons](https://fonts.google.com/icons)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request or open an Issue.
*(Optional: Add contribution guidelines if you have specific requirements.)*

## License

*(Optional: Specify a license for your project, e.g., MIT, Apache 2.0. If you don't add one, standard copyright laws apply. Example:)*
This project is licensed under the MIT License - see the `LICENSE.md` file for details (if you create one).
**Note:** The Caffe model files may have their own licenses; please ensure compliance.
Use code with caution.
Next Steps:
Create requirements.txt:
If you haven't already, after installing the packages in your virtual environment, run:
pip freeze > requirements.txt
Use code with caution.
Bash
This will capture the exact versions of the packages you're using, which is good for reproducibility.
Placeholder Screenshot: Replace placeholder_screenshot.png in the README with an actual screenshot of your application.
Model File Links/Guidance: Update the "Download Model Files" section with specific links or clearer instructions on how users can obtain the .prototxt, .caffemodel, and .npy files. This is crucial for others to be able to run your project.
License File (Optional but Recommended): If you want to formally license your code, create a LICENSE.md file (e.g., with the MIT license text).
GitHub:
Initialize a git repository in your project folder (git init).
Add all your project files (git add .).
Commit your files (git commit -m "Initial commit").
Create a new repository on GitHub.
Link your local repository to the GitHub remote and push (git remote add origin ..., git push -u origin main).