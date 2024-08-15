import json
import os
from PIL import Image, ImageDraw, ImageFont
import argparse

def draw_annotations(json_path):
    # Load the JSON file
    with open(json_path, 'r') as f:
        annotations = json.load(f)

    # Create output folder
    output_folder = os.path.join('/pdf', os.path.splitext(os.path.basename(json_path))[0])
    os.makedirs(output_folder, exist_ok=True)

    # Load a font
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 8)
    except IOError:
        font = ImageFont.load_default()

    for image_path, anns in annotations.items():
        # Open the image
        img = Image.open(os.path.join(image_path))
        draw = ImageDraw.Draw(img)

        for ann in anns:
            # Draw word box in blue
            draw.rectangle(ann['bbox'], outline='blue', width=2)

            # Draw text above the box
            text_position = (ann['bbox'][0], ann['bbox'][1] - 10)
            draw.text(text_position, ann['text'][:20], font=font, fill='blue')

            # Draw character boxes in yellow
            for char in ann['chars']:
                draw.rectangle(char['bbox'], outline='yellow', width=1)

        # Save the annotated image
        output_path = os.path.join(output_folder, f"{os.path.splitext(os.path.basename(image_path))[0]}_with_boxes.jpg")
        img.save(output_path)
        print(f"Saved annotated image: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Draw annotation boxes on images.")
    parser.add_argument("json_path", help="Path to the JSON file containing annotations.")
    args = parser.parse_args()

    draw_annotations(args.json_path)