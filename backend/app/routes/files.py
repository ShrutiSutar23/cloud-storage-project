from fastapi import APIRouter, Depends, UploadFile, File as FastAPIFile, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.supabase_client import supabase
from app.models.user import User
from app.models.file import File
from app.schemas.file import FileResponse
import uuid

router = APIRouter(prefix="/files", tags=["files"])

@router.post("/upload", response_model=FileResponse)
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Read file content into memory
    file_content = await file.read()
    file_size = len(file_content)

    # Create a unique storage path so files never overwrite each other
    unique_name = f"{current_user.id}/{uuid.uuid4()}_{file.filename}"

    # Upload to Supabase Storage bucket named "files"
    try:
        supabase.storage.from_("files").upload(
            unique_name,
            file_content,
            {"content-type": file.content_type}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage upload failed: {str(e)}")

    # Get the public/signed URL reference (we'll keep bucket private, store the path)
    file_url = unique_name

    # Save metadata in the database
    new_file = File(
        name=file.filename,
        size=file_size,
        file_url=file_url,
        owner_id=current_user.id,
        is_deleted=False,
        starred=False
    )
    db.add(new_file)
    db.commit()
    db.refresh(new_file)

    return new_file

@router.get("/{file_id}")
def get_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file_record = db.query(File).filter(File.id == file_id, File.is_deleted == False).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    if file_record.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this file")

    # Generate a temporary signed URL valid for 1 hour
    signed_url = supabase.storage.from_("files").create_signed_url(file_record.file_url, 3600)

    return {
        "file": file_record,
        "download_url": signed_url.get("signedURL")
    }