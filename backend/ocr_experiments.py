import os
import json
import numpy as np
import easyocr
import cv2
from PIL import Image
from surya.ocr import run_ocr
from surya.model.detection.model import load_model as load_detection_model, load_processor as load_detection_processor
from surya.model.recognition.model import load_model as load_recognition_model
from surya.model.recognition.processor import load_processor as load_recognition_processor


from run_models import run_conf_recognition

def run_surya_detection(image_path, det_model, det_processor, rec_model, rec_processor):
    image = Image.open(image_path)
    predictions = run_ocr([image], [["en"]], det_model, det_processor, rec_model, rec_processor)
    return [
        {
            'bbox': det.bbox,
            'text': det.text,
            'confidence': det.confidence
        }
        for det in predictions[0].text_lines
    ]

def run_easyocr_detection(image_path, reader):
    results = reader.readtext(image_path)
    return [
        {
            'bbox': bbox,
            'text': text,
            'confidence': conf
        }
        for (bbox, text, conf) in results
    ]

def run_easyocr_recognition(image_path, bboxes, reader):
    image = cv2.imread(image_path)
    recs = []
    for bbox in bboxes:
        _,text,conf = reader.recognize(np.array(Image.fromarray(image[int(bbox[1]):int(bbox[3]),int(bbox[0]):int(bbox[2])]).convert('L')))[0]
        recs.append({
            'text': text,
            'confidence': conf
        })
    return recs

def run_surya_recognition(image_path, bboxes, rec_model, rec_processor):
    image = Image.open(image_path)
    predictions = run_conf_recognition([image], [["en"]], rec_model, rec_processor, bboxes=[bboxes])
    return [
        {
            'text': pred.text,
            'confidence': pred.confidence
        }
        for pred in predictions[0].text_lines
    ]

def convert_boxes(boxes):
    line_box_coords = []
    for boxx in boxes:
        box = boxx[0]+boxx[1]+boxx[2]+boxx[3]
        x1, y1 = np.min(box[0::2]), np.min(box[1::2])  
        x2, y2 = np.max(box[0::2]), np.max(box[1::2])  
        line_box_coords.append([x1,y1,x2,y2])
    return line_box_coords


def run_experiments(image_path, models):
    results = {}

    # Initialize models
    surya_det_processor, surya_det_model = load_detection_processor(), load_detection_model()
    surya_rec_model, surya_rec_processor = load_recognition_model(), load_recognition_processor()

    easyocr_reader = easyocr.Reader(['en'])

    for detector, recognizers in models.items():
        if detector == 'surya':
            detections = run_surya_detection(image_path, surya_det_model, surya_det_processor, surya_rec_model, surya_rec_processor)
        elif detector == 'easyocr':
            detections = run_easyocr_detection(image_path, easyocr_reader)
        else:
            raise ValueError(f"Unknown detector: {detector}")

        bboxes = [det['bbox'] for det in detections]
        if detector == 'easyocr':
            bboxes = convert_boxes(bboxes)
            
        for recognizer in recognizers:
            if recognizer == 'surya':
                if detector == 'surya':
                    recognitions = [{'text': det['text'], 'confidence': det['confidence']} for det in detections]
                else:
                    recognitions = run_surya_recognition(image_path, bboxes, surya_rec_model, surya_rec_processor)
            elif recognizer == 'easyocr':
                if detector == 'easyocr':
                    recognitions = [{'text': det['text'], 'confidence': det['confidence']} for det in detections]
                else:
                    recognitions = run_easyocr_recognition(image_path, bboxes,easyocr_reader)
            else:
                raise ValueError(f"Unknown recognizer: {recognizer}")

            results[f"{detector}_{recognizer}"] = [
                {
                    'bbox': det['bbox'],
                    'text': rec['text'],
                    'confidence': rec['confidence']
                }
                for det, rec in zip(detections, recognitions)
            ]

    return results

if __name__ == "__main__":
    image_path = "/pdf/processed/survive/page_1.jpg"  
    models = {
        'surya': ['surya', 'easyocr'],
        'easyocr': ['surya', 'easyocr']
    }

    results = run_experiments(image_path, models)
    print(results)
    # Save results
    output_file = "ocr_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Results saved to {output_file}")