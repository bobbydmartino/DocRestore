import json
json_path = '/pdf/annots/Compendium_gt_annots.json'
with open(json_path, 'r') as f:
    annotations = json.load(f)
    
breakpoint()