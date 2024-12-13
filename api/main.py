from fastapi import FastAPI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi import UploadFile, File, HTTPException, Request
import os



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500/"],  # This allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)

@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
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
        
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": f"Error uploading image: {str(e)}", "success": False})

@app.post("/api/funny")
async def funny(request: Request):
    body = await request.json()
    number = int(body.get("number"))
    return {"message":f"funny {number}"}

@app.get("/")
async def root():
    return {"message": "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"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)