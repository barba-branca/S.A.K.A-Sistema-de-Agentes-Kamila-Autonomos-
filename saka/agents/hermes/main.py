import os
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import AzureError

app = FastAPI(
    title="Hermes - File Handler",
    description="Agent responsible for handling file uploads to Azure Blob Storage.",
    version="1.1.0"
)

# Configuration
AZURE_CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING")
AZURE_CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME")

def get_blob_service_client():
    if not AZURE_CONNECTION_STRING:
        return None
    return BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)

@app.get("/health")
def health():
    return {"status": "ok", "service": "hermes"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not AZURE_CONNECTION_STRING or not AZURE_CONTAINER_NAME:
        raise HTTPException(status_code=500, detail="Azure configuration (Connection String or Container Name) is missing.")

    try:
        blob_service_client = get_blob_service_client()

        # Ensure container exists (optional, mostly for dev convenience)
        # try:
        #     blob_service_client.create_container(AZURE_CONTAINER_NAME)
        # except Exception:
        #     pass

        container_client = blob_service_client.get_container_client(AZURE_CONTAINER_NAME)

        # Generate a unique key using UUID to prevent collisions
        file_extension = os.path.splitext(file.filename)[1]
        blob_name = f"{uuid.uuid4()}{file_extension}"

        # Upload file
        blob_client = container_client.get_blob_client(blob_name)

        # file.file is a SpooledTemporaryFile. upload_blob supports read()
        blob_client.upload_blob(file.file, overwrite=True)

        return {
            "filename": blob_name,
            "message": "Upload successful",
            "container": AZURE_CONTAINER_NAME,
            "location": blob_client.url
        }

    except AzureError as e:
        raise HTTPException(status_code=500, detail=f"Azure Storage error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
