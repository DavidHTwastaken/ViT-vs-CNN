from fastapi import FastAPI
import uvicorn
from transformers import ViTImageProcessor, ViTForImageClassification, BitImageProcessor, BitForImageClassification
import torch
from fastapi.middleware.cors import CORSMiddleware
from fastapi import UploadFile, File, HTTPException, Request, Form
import os
import pandas as pd

DEVICE = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')

# Both ViT and BiT models classify images into one of 1000 classes from ImageNet
processor = ViTImageProcessor.from_pretrained('google/vit-base-patch16-224')
vit_model = ViTForImageClassification.from_pretrained(
    'google/vit-base-patch16-224').eval().to(DEVICE)
feature_extractor = BitImageProcessor.from_pretrained("google/bit-50")
bit_model = BitForImageClassification.from_pretrained("google/bit-50").eval().to(DEVICE)

def classify(model, processor, image):
    inputs = processor(images=image, return_tensors="pt")
    outputs = model(**inputs)
    logits = outputs.logits
    predicted_class_idx = logits.argmax(-1).item()
    confidence = torch.nn.Softmax(logits)[predicted_class_idx]
    return predicted_class_idx, confidence

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500/"],  # This allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)


def get_description_by_index(file_path, row_index):
    with open(file_path, 'r') as file:
        lines = file.readlines()  # Read all lines into a list
    
    if 0 <= row_index < len(lines):  # Check if the index is valid
        line = lines[row_index].strip()  # Get the specific line and remove extra spaces
        parts = line.split(' ', 1)  # Split the line into ID and description
        if len(parts) == 2:
            return parts[1]  # Return the description part (everything after the ID)
    return None  # Return None if the index is invalid

@app.post("/api/upload")
async def upload(file: UploadFile = File(...), model: str = Form(...)):
    """
    Request object
    {
        file: uploaded file
    }

    Response object
    {
        success: True
    }
    """

    try: 
        print("Uploaded file name:", file.filename)
        parent_directory = os.path.dirname(os.path.dirname(__file__))
        save_path = os.path.join(parent_directory, file.filename)
        with open(save_path, "wb") as f:
            f.write(await file.read())

        if model == "transformer":
            print("using transformer")
            predicted_class, confidence = classify(vit_model, processor, save_path)
        else:
            print("using image cnn")
            predicted_class, confidence = classify(bit_model, feature_extractor, save_path)

        description = get_description_by_index("../LOC_synset_mapping.txt", predicted_class)

        return {"success": True, "confidence": confidence, "description": description}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": f"Error uploading image: {str(e)}", "success": False})

@app.post("/api/funny")
async def funny(request: Request):
    body = await request.json()
    number = int(body.get("number"))
    return {"message":f"funny {number}"}

@app.get("/")
async def root():
    return "Hello World!"
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)