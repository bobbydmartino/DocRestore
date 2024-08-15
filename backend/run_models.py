from PIL import Image

# from surya.ocr import run_ocr
# from surya.model.detection import segformer
# from surya.model.recognition.model import load_model
# from surya.model.recognition.processor import load_processor

# from surya.layout import batch_layout_detection
# from surya.detection import batch_text_detection
# from surya.model.detection.segformer import load_model as lm
# from surya.model.detection.segformer import  load_processor as lp
# from surya.settings import settings


from typing import List

from surya.detection import batch_text_detection
from surya.input.processing import slice_polys_from_image, slice_bboxes_from_image, convert_if_not_rgb
from surya.postprocessing.text import sort_text_lines
from surya.recognition import batch_recognition
from surya.schema import TextLine, OCRResult


def run_conf_recognition(images: List[Image.Image], langs: List[List[str]], rec_model, rec_processor, bboxes: List[List[List[int]]] = None, polygons: List[List[List[List[int]]]] = None, batch_size=None) -> List[OCRResult]:
    # Polygons need to be in corner format - [[x1, y1], [x2, y2], [x3, y3], [x4, y4]], bboxes in [x1, y1, x2, y2] format
    assert bboxes is not None or polygons is not None
    assert len(images) == len(langs), "You need to pass in one list of languages for each image"

    images = convert_if_not_rgb(images)

    slice_map = []
    all_slices = []
    all_langs = []
    for idx, (image, lang) in enumerate(zip(images, langs)):
        if polygons is not None:
            slices = slice_polys_from_image(image, polygons[idx])
        else:
            slices = slice_bboxes_from_image(image, bboxes[idx])
        slice_map.append(len(slices))
        all_slices.extend(slices)
        all_langs.extend([lang] * len(slices))

    rec_predictions, confidence_scores = batch_recognition(all_slices, all_langs, rec_model, rec_processor, batch_size=batch_size)

    predictions_by_image = []
    slice_start = 0
    for idx, (image, lang) in enumerate(zip(images, langs)):
        slice_end = slice_start + slice_map[idx]
        image_lines = rec_predictions[slice_start:slice_end]
        line_confidences = confidence_scores[slice_start:slice_end]
        slice_start = slice_end

        text_lines = []
        for i in range(len(image_lines)):
            if polygons is not None:
                poly = polygons[idx][i]
            else:
                bbox = bboxes[idx][i]
                poly = [[bbox[0], bbox[1]], [bbox[2], bbox[1]], [bbox[2], bbox[3]], [bbox[0], bbox[3]]]

            text_lines.append(TextLine(
                text=image_lines[i],
                confidence=line_confidences[i],
                polygon=poly
            ))

        pred = OCRResult(
            text_lines=text_lines,
            languages=lang,
            image_bbox=[0, 0, image.size[0], image.size[1]]
        )
        predictions_by_image.append(pred)

    return predictions_by_image



def compute_area(bbox):
    """Compute the area of a bounding box."""
    x0, y0, x1, y1 = bbox
    return (x1 - x0 + 1) * (y1 - y0 + 1)


def compute_overlap_area(bbox1, bbox2):
    """
    Compute the area of overlap between two bounding boxes.

    Bounding boxes are formatted as [x0, y0, x1, y1]
    """
    x0_1, y0_1, x1_1, y1_1 = bbox1
    x0_2, y0_2, x1_2, y1_2 = bbox2

    # Calculate overlap area
    overlap_x0 = max(x0_1, x0_2)
    overlap_y0 = max(y0_1, y0_2)
    overlap_x1 = min(x1_1, x1_2)
    overlap_y1 = min(y1_1, y1_2)

    overlap_width = max(0, overlap_x1 - overlap_x0 + 1)
    overlap_height = max(0, overlap_y1 - overlap_y0 + 1)

    overlap_area = overlap_width * overlap_height
    return overlap_area

def is_contained(bbox1, bbox2):
    """Check if bbox1 is contained within bbox2."""
    x0_1, y0_1, x1_1, y1_1 = bbox1
    x0_2, y0_2, x1_2, y1_2 = bbox2

    return x0_1 >= x0_2 and y0_1 >= y0_2 and x1_1 <= x1_2 and y1_1 <= y1_2

def filter_contained_paragraphs(paragraph_bboxes):
    """Filter out paragraph boxes that are fully contained within another box."""
    filtered_bboxes = []
    for i, bbox1 in enumerate(paragraph_bboxes):
        contained = False
        for j, bbox2 in enumerate(paragraph_bboxes):
            if i != j and is_contained(bbox1, bbox2):
                contained = True
                break
        if not contained:
            filtered_bboxes.append(bbox1)
    return filtered_bboxes

def assign_predictions_to_paragraphs(image_predictions, paragraph_bboxes):
    """Assign each prediction to the paragraph with the highest overlap (over 50%)."""
    assigned_paragraphs = {tuple(bbox): [] for bbox in paragraph_bboxes}
    extra_paragraphs = []
    for prediction in image_predictions:
        best_overlap = 0
        best_paragraph = None
        prediction_bbox = prediction['bbox']
        prediction_area = compute_area(prediction_bbox)
        for paragraph_bbox in paragraph_bboxes:
            overlap_area = compute_overlap_area(prediction_bbox, paragraph_bbox)
            overlap_percentage = overlap_area / prediction_area
            if overlap_percentage > 0.5 and overlap_percentage > best_overlap:
                best_overlap = overlap_percentage
                best_paragraph = paragraph_bbox
        if best_paragraph:
            assigned_paragraphs[tuple(best_paragraph)].append(prediction)
        else:
            extra_paragraphs.append({'bbox': prediction_bbox, 'text': prediction['text']})
    return assigned_paragraphs, extra_paragraphs

def sort_and_concatenate_predictions(assigned_paragraphs, extra_paragraphs):
    """Sort the predictions within each paragraph and concatenate the text."""
    result = []
    for paragraph_bbox, predictions in assigned_paragraphs.items():
        predictions = sorted(predictions, key=lambda x: (x['bbox'][1], x['bbox'][0]))
        combined_text = " ".join([prediction['text'] for prediction in predictions])
        result.append({'bbox': paragraph_bbox, 'text': combined_text})
    result.extend(extra_paragraphs)
    return result

def process_image_predictions(image_predictions, para_bboxes):
    filtered_paragraphs = filter_contained_paragraphs(para_bboxes)
    assigned_paragraphs, extra_paragraphs = assign_predictions_to_paragraphs(image_predictions, filtered_paragraphs)
    final_predictions = sort_and_concatenate_predictions(assigned_paragraphs, extra_paragraphs)
    return final_predictions


# class suryaSystem:
#     def __init__(self,models):
#         self.langs = ['en']
#         self.det_processor, self.det_model = segformer.load_processor(), segformer.load_model()
#         self.rec_model, self.rec_processor = load_model(), load_processor()
#         self.lay_model = lm(checkpoint=settings.LAYOUT_MODEL_CHECKPOINT)
#         self.lay_processor = lp(checkpoint=settings.LAYOUT_MODEL_CHECKPOINT)
#         self.line_model = lm()
#         self.line_processor = lp()
        
#     def runOCR(self,image_path,paragraphification=False):
#         annots = {}
#         annots[image_path] = []
#         para_annots = {}
#         para_annots[image_path] = []
        
#         image = Image.open(image_path)
#         predictions = run_ocr([image], [self.langs], self.det_model, self.det_processor, self.rec_model, self.rec_processor)
#         for pred in predictions:
#             detects = pred.dict()['text_lines']
#             for det in detects:
#                 annots[image_path].append(
#                     {
#                         'bbox':det['bbox'],
#                         'text':det['text'],
#                         'chars':[],
#                         'conf':det['confidence']
#                     }
#                 )
                
#         if paragraphification:
#             line_predictions = batch_text_detection([image], lm(), lp())
#             layout_predictions = batch_layout_detection([image], self.lay_model, self.lay_processor, line_predictions)
#             layout_analysis = layout_predictions[0].dict()
#             para_bboxes = [x['bbox'] for x in layout_analysis['bboxes']]
#             para_annots[image_path] = process_image_predictions(annots[image_path], para_bboxes)
        
#         return annots, para_annots


################### EASY OCR example ###############################################

# import easyocr 

# reader = easyocr.Reader(['en'],gpu=True)
# reader.readtext(image_path)


# def get_line_boxes(image_path,reader):
#     total_detections = reader.readtext(image_path)
#     line_box_coords = []
#     for boxx in [x[0] for x in total_detections]:
#         box = boxx[0]+boxx[1]+boxx[2]+boxx[3]
#         x1, y1 = np.min(box[0::2]), np.min(box[1::2])  
#         x2, y2 = np.max(box[0::2]), np.max(box[1::2])  
#         line_box_coords.append([x1,y1,x2,y2])
#     return line_box_coords


# def get_word_boxes_ocr(image_path, line_box_coords,reader):
#     img = cv2.imread(image_path)
#     image_dict = {}
#     for (x1,y1,x2,y2) in line_box_coords:
#         image_dict[(x1,y1,x2,y2)] = {}
    
#     word_boxes = reader.get_textbox(reader.get_detector(reader.getDetectorPath('craft')).to(device),
#                                   img,
#                                   canvas_size=2560,
#                                   mag_ratio=1,
#                                   text_threshold=0.7,
#                                   link_threshold=0.4,
#                                   low_text=0.4,
#                                   poly=False,
#                                   device=device)[0]
#     word_box_coords = []
#     for box in word_boxes:
#         x1, y1 = np.min(box[0::2]), np.min(box[1::2])  
#         x2, y2 = np.max(box[0::2]), np.max(box[1::2])  
#         word_box_coords.append([x1,y1,x2,y2])

#     new_word_boxes = []
#     for word in word_box_coords:
#         line_box = []
#         max_overlap = 0
#         new_word = ""
#         for line in line_box_coords:
#             area = compute_overlap_area(line,word)
#             if area > max_overlap:
#                 line_box = line
#                 max_overlap = area
#         if len(line_box) > 0:
#             new_word = [max(0,word[0]-3),min(line_box[1],word[1])+3,word[2]+3,max(word[3],line_box[3])-3]
#             image_dict[tuple(line_box)][tuple(new_word)] = {}
#     return image_dict,img
