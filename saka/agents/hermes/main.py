import os
import boto3
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from botocore.exceptions import NoCredentialsError, ClientError

app = FastAPI(
    title="Hermes - File Handler",
    description="Agent responsible for handling file uploads to AWS S3.",
    version="1.0.0"
)

# Configuration
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION_NAME = os.getenv("AWS_REGION_NAME", "us-east-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

# Initialize S3 Client
def get_s3_client():
    if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET_NAME]):
        # Allow running without creds for health checks, but uploads will fail
        return None
    return boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION_NAME
    )

@app.get("/health")
def health():
    return {"status": "ok", "service": "hermes"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    s3 = get_s3_client()
    if not s3:
        raise HTTPException(status_code=500, detail="AWS credentials or bucket name not configured.")

    try:
        # Generate a unique key using UUID to prevent collisions
        file_extension = os.path.splitext(file.filename)[1]
        file_key = f"{uuid.uuid4()}{file_extension}"

        # Upload file
        # file.file is a SpooledTemporaryFile
        s3.upload_fileobj(
            file.file,
            S3_BUCKET_NAME,
            file_key
        )

        # Generate Presigned URL (optional, useful for verification)
        # url = s3.generate_presigned_url('get_object', Params={'Bucket': S3_BUCKET_NAME, 'Key': file_key})

        return {
            "filename": file_key,
            "message": "Upload successful",
            "bucket": S3_BUCKET_NAME,
            "location": f"s3://{S3_BUCKET_NAME}/{file_key}"
        }

    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS credentials not found.")
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
