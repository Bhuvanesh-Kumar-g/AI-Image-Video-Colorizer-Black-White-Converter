# D:\PROJECT\ML b&w colorizer Project\app.py
import cv2
import numpy as np
import os
import time
# import threading # Not strictly needed for Flask's default single-threaded dev server
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
        print(f"Created directory: {folder}")

# --- Model Loading ---
proto_path = os.path.join(MODELS_DIR, "colorization_deploy_v2.prototxt")
weights_path = os.path.join(MODELS_DIR, "colorization_release_v2.caffemodel")
pts_in_hull_path = os.path.join(MODELS_DIR, "pts_in_hull.npy")

if not all(os.path.exists(p) for p in [proto_path, weights_path, pts_in_hull_path]):
    raise FileNotFoundError("One or more model files are missing. Check the 'models' directory.")

print("Loading Caffe model...")
net = cv2.dnn.readNetFromCaffe(proto_path, weights_path)
print("Loading cluster centers (pts_in_hull.npy)...")
pts_in_hull = np.load(pts_in_hull_path).transpose().reshape(2, 313, 1, 1).astype(np.float32)
net.getLayer(net.getLayerId("class8_ab")).blobs = [pts_in_hull]
net.getLayer(net.getLayerId("conv8_313_rh")).blobs = [np.full((1, 313), 2.606, np.float32)]
print("✅ Model loaded successfully.")

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

# --- Flask App ---
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # Increased to 200 MB limit for uploads

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

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        original_filename = secure_filename(file.filename)
        input_filepath = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
        file.save(input_filepath)

        print(f"Processing {original_filename} in mode: {mode}")
        start_time = time.time()

        base, ext = os.path.splitext(original_filename)
        
        if ext.lower() in ['.jpg', '.jpeg', '.png']:
             output_ext = ext 
        elif ext.lower() in ['.mp4', '.avi', '.mov', '.mkv']:
             output_ext = ".mp4" # Standardize video output to mp4
        else:
            # This case should ideally be caught by allowed_file, but as a fallback:
            try:
                os.remove(input_filepath)
            except OSError as e_rem:
                print(f"Error removing uploaded file {input_filepath} for unsupported type: {e_rem}")
            return jsonify({'error': 'Unsupported file type during processing'}), 400


        output_filename = f"{mode}_{base}{output_ext}"
        output_filepath = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)

        processing_message = ""
        try:
            if output_ext.lower() in ['.jpg', '.jpeg', '.png']:
                img = cv2.imread(input_filepath)
                if img is None:
                    raise ValueError("Failed to read image.")
                
                if mode == "colorize":
                    out_img = colorize_frame_api(img)
                else:
                    out_img = convert_to_bw_api(img)
                cv2.imwrite(output_filepath, out_img)
                processing_message = "Image processing complete."

            elif output_ext.lower() == '.mp4':
                cap = cv2.VideoCapture(input_filepath)
                if not cap.isOpened():
                    raise ValueError(f"Failed to open video: {input_filepath}")

                fps = cap.get(cv2.CAP_PROP_FPS)
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                
                output_processing_width = 640
                original_frame_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                original_frame_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

                if original_frame_width == 0 or original_frame_height == 0:
                    cap.release()
                    raise ValueError("Video has zero width or height.")
                
                output_processing_height = int(original_frame_height * output_processing_width / original_frame_width)

                fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
                video_writer = cv2.VideoWriter(output_filepath, fourcc, fps, (output_processing_width, output_processing_height))

                if not video_writer.isOpened():
                    cap.release()
                    raise IOError(f"Failed to open VideoWriter for {output_filepath}")

                frame_idx = 0
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    frame_idx += 1
                    
                    frame_for_processing = cv2.resize(frame, (output_processing_width, output_processing_height))
                    
                    if mode == "colorize":
                        processed_frame = colorize_frame_api(frame_for_processing)
                    else:
                        processed_frame = convert_to_bw_api(frame_for_processing)
                    video_writer.write(processed_frame)
                    if frame_idx % 60 == 0: print(f"Processed frame {frame_idx}/{total_frames}")

                cap.release()
                video_writer.release()
                print("🎬 Video streams closed.")

                # **MODIFIED: Check if video file exists and is not empty**
                if not os.path.exists(output_filepath) or os.path.getsize(output_filepath) == 0:
                    error_msg = f"Processed video file {output_filepath} was not created or is empty."
                    print(f"⚠️ WARNING: {error_msg}")
                    raise IOError(error_msg) # Make it an error to be caught by the main try-except
                else:
                    print(f"✅ Video processing complete! Output saved at: {output_filepath} (Size: {os.path.getsize(output_filepath)} bytes)")
                processing_message = f"Video processing complete. {frame_idx} frames processed."
            else:
                # Should not happen due to earlier checks
                raise ValueError(f"Unexpected output extension: {output_ext}")


            processing_time = time.time() - start_time
            print(f"Finished processing. Time: {processing_time:.2f}s. Output: {output_filename}")
            
            try:
                os.remove(input_filepath)
                print(f"Removed uploaded file: {input_filepath}")
            except OSError as e:
                print(f"Error removing uploaded file {input_filepath}: {e}")

            return jsonify({
                'message': processing_message,
                'processed_file_url': f'/processed/{output_filename}',
                'filename': output_filename,
                'is_video': output_ext.lower() == ".mp4"
            })

        except Exception as e:
            print(f"Error processing file: {e}")
            import traceback
            traceback.print_exc()
            if os.path.exists(input_filepath):
                try:
                    os.remove(input_filepath)
                except OSError as e_rem:
                    print(f"Error removing uploaded file {input_filepath} after error: {e_rem}")
            # Also try to remove partially created output file on error
            if 'output_filepath' in locals() and os.path.exists(output_filepath):
                try:
                    os.remove(output_filepath)
                    print(f"Removed partially created/problematic output file: {output_filepath}")
                except OSError as e_rem_out:
                    print(f"Error removing output file {output_filepath} after error: {e_rem_out}")
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'File type not allowed'}), 400

@app.route('/processed/<filename>')
def send_processed_file(filename):
    # Add Cache-Control headers to prevent aggressive caching during development/testing
    response = send_from_directory(app.config['PROCESSED_FOLDER'], filename)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)