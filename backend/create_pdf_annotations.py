from pdfminer.layout import LAParams, LTTextBox
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
import cv2
import ubelt as ub
import pdfminer
import json
import os
import sys
from tqdm import tqdm

# Draw bounding boxes on the image
def rescale_bbox(image_shape, bbox, rescale_factor_x, rescale_factor_y):
    # Rescale the coordinates
    x0 = int(bbox[0] * rescale_factor_x)
    y0 = int(image_shape - bbox[3] * rescale_factor_y)
    # y0 = int(bbox[1] * rescale_factor_y)
    x1 = int(bbox[2] * rescale_factor_x)
    y1 = int(image_shape - bbox[1] * rescale_factor_y)
    # y1 = int(bbox[3] * rescale_factor_y)

    return [x0, y0, x1, y1]


def create_pdf_images_and_annotations(pdf_name,output_path):
    fp = open(f'/pdf/{pdf_name}.pdf', 'rb')

    # Check if image folder exists
    image_folder_path = f"/pdf/processed/{pdf_name}"
    ub.ensuredir(image_folder_path)

    rsrcmgr = PDFResourceManager()
    laparams = LAParams()
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    pages = PDFPage.get_pages(fp)

    num_pages = len(os.listdir(image_folder_path))
    num_padding = len(str(num_pages))

    pdf_pages = {}

    for pn, page in tqdm(enumerate(pages), total=num_pages):
        pagenum = pn + 1
        # Read in image using corresponding name
        image_path = f"{image_folder_path}/page_{pagenum}.jpg"
        image = cv2.imread(image_path)

        pdf_pages[image_path] = []
        interpreter.process_page(page)
        layout = device.get_result()

        cropbox = page.attrs['CropBox']
        rescale_factor_x = image.shape[1] / cropbox[2]
        rescale_factor_y = image.shape[0] / cropbox[3]

        for lobj in layout:
            if isinstance(lobj, LTTextBox):
                # Total bounding box
                ann_num = len(pdf_pages[image_path])
                pdf_pages[image_path].append({
                    'text': lobj.get_text(),
                    'bbox': rescale_bbox(image.shape[0], lobj.bbox, rescale_factor_x, rescale_factor_y),
                    'chars': [],
                })

                # per character bounding box
                char_bboxes = [(x.get_text(), x.bbox) for y in lobj._objs for x in y._objs if type(x) is pdfminer.layout.LTChar]
                for bbox in char_bboxes:
                    # [len(pdf_pages[image_path][ann_num]['chars'])]
                    pdf_pages[image_path][ann_num]['chars'].append({
                        'text': bbox[0],
                        'bbox': rescale_bbox(image.shape[0], bbox[1], rescale_factor_x, rescale_factor_y),
                    })

    
    with open(output_path, 'w') as f:
        json.dump(pdf_pages, f)
    # return pdf_pages


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: script_name.py <pdf_name>")
        sys.exit(1)

    pdf_name = sys.argv[1]
    file_path = f"/pdf/{pdf_name}.pdf"
    ub.ensuredir('/pdf/annots/')
    output_path = f"/pdf/annots/{os.path.splitext(pdf_name)[0]}/{os.path.splitext(pdf_name)[0]}_gt_annots.json"

    if not os.path.exists(file_path):
        print(f"Error: File {pdf_name} does not exist in /data/pdfs/")
        sys.exit(1)

    if not file_path.lower().endswith('.pdf'):
        print("Error: The provided file is not a PDF.")
        sys.exit(1)

    try:
        create_pdf_images_and_annotations(pdf_name,output_path)
        print(f"Successfully created annotations at {output_path}")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)