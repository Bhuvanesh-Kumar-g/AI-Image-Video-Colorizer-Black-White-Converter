import cv2
import numpy as np
import os
import threading
import time
import uuid
import shutil
from flask import Flask, request, jsonify, send_from_directory, render_template
from werkzeug.utils import secure_filename

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
PROCESSED_FOLDER = os.path.join(BASE_DIR, 'processed_files')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'mp4', 'avi', 'mov', 'mkv'}

# Create necessary directories
for folder in [MODELS_DIR, UPLOAD_FOLDER, PROCESSED_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# --- Model Loading ---
proto_path = os.path.join(MODELS_DIR, "colorization_deploy_v2.prototxt")
weights_path = os.path.join(MODELS_DIR, "colorization_release_v2.caffemodel")
pts_in_hull_path = os.path.join(MODELS_DIR, "pts_in_hull.npy")

if not all(os.path.exists(p) for p in [proto_path, weights_path, pts_in_hull_path]):
    raise FileNotFoundError("One or more model files are missing.")

print("Loading Caffe model...")
net = cv2.dnn.readNetFromCaffe(proto_path, weights_path)
pts_in_hull = np.load(pts_in_hull_path).transpose().reshape(2, 313, 1, 1).astype(np.float32)
net.getLayer(net.getLayerId("class8_ab")).blobs = [pts_in_hull]
net.getLayer(net.getLayerId("conv8_313_rh")).blobs = [np.full((1, 313), 2.606, np.float32)]
print("✅ Model loaded successfully.")

# --- Global Dictionary to store task status ---
# In a production app, use Redis or a Database. For this, a dict is fine.
tasks = {}

# --- Processing Functions ---
def colorize_frame_api(frame_bgr):
    (orig_h, orig_w) = frame_bgr.shape[:2]
    frame_bgr_norm = (frame_bgr / 255.0).astype(np.float32)
    img_lab = cv2.cvtColor(frame_bgr_norm, cv2.COLOR_BGR2Lab)
    img_l = img_lab[:, :, 0]
    input_l_resized = cv2.resize(img_l, (224, 224))
    input_l_resized -= 50
    net.setInput(cv2.dnn.blobFromImage(input_l_resized))
    pred_ab = net.forward()[0, :, :, :].transpose((1, 2, 0))
    pred_ab_resized = cv2.resize(pred_ab, (orig_w, orig_h))
    output_lab = np.concatenate([img_l[:, :, np.newaxis], pred_ab_resized], axis=2)
    output_bgr_norm = cv2.cvtColor(output_lab, cv2.COLOR_Lab2BGR)
    output_bgr = np.clip(output_bgr_norm, 0, 1) * 255
    return output_bgr.astype(np.uint8)

def convert_to_bw_api(frame_bgr):
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

# --- Background Worker ---
def background_worker(task_id, input_filepath, mode, original_filename):
    tasks[task_id]['status'] = 'processing'
    tasks[task_id]['log'] = f"Starting processing for {original_filename}..."
    
    try:
        base, ext = os.path.splitext(original_filename)
        output_ext = ".mp4" if ext.lower() in ['.mp4', '.avi', '.mov', '.mkv'] else ext
        output_filename = f"{mode}_{base}{output_ext}"
        output_filepath = os.path.join(PROCESSED_FOLDER, output_filename)

        if output_ext.lower() in ['.jpg', '.jpeg', '.png']:
            img = cv2.imread(input_filepath)
            tasks[task_id]['log'] = "Processing image..."
            if mode == "colorize":
                out_img = colorize_frame_api(img)
            else:
                out_img = convert_to_bw_api(img)
            cv2.imwrite(output_filepath, out_img)
            tasks[task_id]['log'] = "Image processing complete."

        elif output_ext.lower() == '.mp4':
            cap = cv2.VideoCapture(input_filepath)
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Reduce resolution slightly for speed if needed, or keep original ratio
            output_processing_width = 640
            original_frame_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            original_frame_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            output_processing_height = int(original_frame_height * output_processing_width / original_frame_width)

            try:
                fourcc = cv2.VideoWriter_fourcc(*'avc1')
            except:
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')

            video_writer = cv2.VideoWriter(output_filepath, fourcc, fps, (output_processing_width, output_processing_height))
            
            # If avc1 failed to initialize, fallback to mp4v immediately
            if not video_writer.isOpened():
                print("H.264 codec not found, falling back to mp4v (Browser playback might fail).")
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                video_writer = cv2.VideoWriter(output_filepath, fourcc, fps, (output_processing_width, output_processing_height))

            frame_idx = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                frame_idx += 1
                
                # Update Log every 10 frames to avoid spamming the dict
                if frame_idx % 10 == 0 or frame_idx == 1:
                    tasks[task_id]['log'] = f"Processed frame {frame_idx}/{total_frames}"
                    tasks[task_id]['progress'] = int((frame_idx / total_frames) * 100)

                frame_for_processing = cv2.resize(frame, (output_processing_width, output_processing_height))
                
                if mode == "colorize":
                    processed_frame = colorize_frame_api(frame_for_processing)
                else:
                    processed_frame = convert_to_bw_api(frame_for_processing)
                video_writer.write(processed_frame)

            cap.release()
            video_writer.release()
            tasks[task_id]['log'] = "Video streams closed. Finalizing..."

        # Cleanup
        if os.path.exists(input_filepath):
            os.remove(input_filepath)

        tasks[task_id]['status'] = 'completed'
        tasks[task_id]['log'] = "Processing complete!"
        tasks[task_id]['result'] = {
            'url': f'/processed/{output_filename}',
            'filename': output_filename,
            'is_video': output_ext.lower() == ".mp4"
        }

    except Exception as e:
        print(f"Error: {e}")
        tasks[task_id]['status'] = 'error'
        tasks[task_id]['log'] = f"Error: {str(e)}"

# --- Flask App ---
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_media_route():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    mode = request.form.get('mode', 'colorize')

    if file and allowed_file(file.filename):
        original_filename = secure_filename(file.filename)
        input_filepath = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
        file.save(input_filepath)

        # Generate Task ID
        task_id = str(uuid.uuid4())
        tasks[task_id] = {'status': 'queued', 'log': 'Initializing...', 'progress': 0}

        # Start Thread
        thread = threading.Thread(target=background_worker, args=(task_id, input_filepath, mode, original_filename))
        thread.start()

        return jsonify({'task_id': task_id})
    else:
        return jsonify({'error': 'Invalid file'}), 400

@app.route('/status/<task_id>')
def get_status(task_id):
    if task_id in tasks:
        return jsonify(tasks[task_id])
    return jsonify({'error': 'Task not found'}), 404

@app.route('/processed/<filename>')
def send_processed_file(filename):
    response = send_from_directory(app.config['PROCESSED_FOLDER'], filename)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
