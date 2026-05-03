import pickle, gzip, json, os

meta_path = 'models/model_metadata.json'
if os.path.exists(meta_path):
    with open(meta_path, 'r') as f:
        meta = json.load(f)
    print("Accuracy from metadata:", meta)
else:
    print("No metadata file found")