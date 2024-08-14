import os
import time
import threading
import schedule
from flask import Flask, jsonify, send_file, request  
from flask_cors import CORS
import pypdfium2 as pdfium
import logging
# from ocr_experiments import OCRExperiment

app = Flask(__name__)
CORS(app)

PDF_FOLDER = '/pdf'
PROCESSED_FOLDER = '/pdf/processed'
LOG_FILE = '/var/log/pdf_processor.log'

# Set up logging
logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

def process_pdfs():
    if not os.path.exists(PROCESSED_FOLDER):
        os.makedirs(PROCESSED_FOLDER)

    activity_occurred = False

    for filename in os.listdir(PDF_FOLDER):
        if filename.lower().endswith('.pdf'):
            pdf_path = os.path.join(PDF_FOLDER, filename)
            output_folder = os.path.join(PROCESSED_FOLDER, os.path.splitext(filename)[0])

            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
                logging.info(f"Processing {filename}...")
                activity_occurred = True
                
                try:
                    logging.info(f"converting {filename}")
                    pdf = pdfium.PdfDocument(pdf_path)
                    for i in range(len(pdf)):
                        page = pdf[i]
                        image = page.render(scale=4).to_pil()
                        image.save(os.path.join(output_folder, f'page_{i+1}.jpg'))
                        logging.info(f"saving {os.path.join(output_folder, f'page_{i+1}.jpg')}")
                    logging.info(f"Finished processing {filename}")
                except Exception as e:
                    logging.error(f"Error processing {filename}: {str(e)}")

    if activity_occurred:
        logging.info("PDF processing completed.")

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

@app.route('/api/documents', methods=['GET'])
def list_documents():
    documents = [d for d in os.listdir(PROCESSED_FOLDER) if os.path.isdir(os.path.join(PROCESSED_FOLDER, d))]
    return jsonify({"documents": documents})

@app.route('/api/document/<doc_name>/pages', methods=['GET'])
def get_document_pages(doc_name):
    doc_path = os.path.join(PROCESSED_FOLDER, doc_name)
    if not os.path.exists(doc_path):
        return jsonify({"error": "Document not found"}), 404
    
    pages = [f for f in os.listdir(doc_path) if f.lower().endswith('.jpg')]
    pages.sort(key=lambda x: int(x.split('_')[1].split('.')[0]))  # Sort by page number
    return jsonify({"pages": pages})

@app.route('/api/document/<doc_name>/page/<page_name>', methods=['GET'])
def get_page_image(doc_name, page_name):
    image_path = os.path.join(PROCESSED_FOLDER, doc_name, page_name)
    if not os.path.exists(image_path):
        return jsonify({"error": "Image not found"}), 404
    
    return send_file(image_path, mimetype='image/jpeg')

@app.route('/api/process_pdfs', methods=['POST'])
def trigger_process_pdfs():
    try:
        process_pdfs()
        return jsonify({"message": "PDF processing completed successfully"}), 200
    except Exception as e:
        logging.error(f"Error in manual PDF processing: {str(e)}")
        return jsonify({"error": "An error occurred during PDF processing"}), 500


# @app.route('/api/run_ocr_experiments', methods=['POST'])
# def run_ocr_experiments():
#     data = request.json
#     pdf_name = data.get('pdf_name')
#     models = data.get('models', {})

#     if not pdf_name:
#         return jsonify({"error": "PDF name is required"}), 400

#     try:
#         experiment = OCRExperiment()
#         experiment.run_experiments(pdf_name, models)
#         return jsonify({"message": f"OCR experiments completed for {pdf_name}"}), 200
#     except FileNotFoundError as e:
#         return jsonify({"error": str(e)}), 404
#     except Exception as e:
#         logging.error(f"Error in OCR experiments: {str(e)}")
#         return jsonify({"error": "An error occurred during OCR experiments"}), 500



if __name__ == '__main__':
    # Schedule the PDF processing job
    schedule.every(5).minutes.do(process_pdfs)

    # Run the scheduler in a separate thread
    scheduler_thread = threading.Thread(target=run_schedule)
    scheduler_thread.start()

    # Run the initial PDF processing
    process_pdfs()

    # Start the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)