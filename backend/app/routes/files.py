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

@router.get("/search/query", response_model=list[FileResponse])
def search_files(
    q: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    results = db.query(File).filter(
        File.owner_id == current_user.id,
        File.is_deleted == False,
        File.name.ilike(f"%{q}%")
    ).all()
    return results

from app.schemas.file import FileResponse
from pydantic import BaseModel
from typing import Optional

class FileRename(BaseModel):
    name: str

class FileMove(BaseModel):
    folder_id: Optional[str] = None

@router.get("", response_model=list[FileResponse])
def list_all_files(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(File).filter(
        File.owner_id == current_user.id
    ).all()


@router.put("/{file_id}/rename", response_model=FileResponse)
def rename_file(
    file_id: str,
    update: FileRename,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file_record = db.query(File).filter(
        File.id == file_id,
        File.owner_id == current_user.id
    ).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    file_record.name = update.name
    db.commit()
    db.refresh(file_record)
    return file_record


@router.put("/{file_id}/move", response_model=FileResponse)
def move_file(
    file_id: str,
    move: FileMove,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file_record = db.query(File).filter(
        File.id == file_id,
        File.owner_id == current_user.id
    ).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    file_record.folder_id = move.folder_id
    db.commit()
    db.refresh(file_record)
    return file_record


@router.delete("/{file_id}")
def soft_delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file_record = db.query(File).filter(
        File.id == file_id,
        File.owner_id == current_user.id
    ).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    file_record.is_deleted = True
    db.commit()
    return {"message": "File moved to trash"}

@router.put("/{file_id}/star", response_model=FileResponse)
def toggle_star(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file_record = db.query(File).filter(
        File.id == file_id,
        File.owner_id == current_user.id
    ).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    file_record.starred = not file_record.starred
    db.commit()
    db.refresh(file_record)
    return file_record


@router.get("/starred/all", response_model=list[FileResponse])
def list_starred_files(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(File).filter(
        File.owner_id == current_user.id,
        File.starred == True,
        File.is_deleted == False
    ).all()

@router.get("/trash/all", response_model=list[FileResponse])
def list_trash(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(File).filter(
        File.owner_id == current_user.id,
        File.is_deleted == True
    ).all()


@router.put("/{file_id}/restore", response_model=FileResponse)
def restore_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file_record = db.query(File).filter(
        File.id == file_id,
        File.owner_id == current_user.id,
        File.is_deleted == True
    ).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found in trash")

    file_record.is_deleted = False
    db.commit()
    db.refresh(file_record)
    return file_record


@router.delete("/{file_id}/permanent")
def permanent_delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file_record = db.query(File).filter(
        File.id == file_id,
        File.owner_id == current_user.id,
        File.is_deleted == True
    ).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found in trash")

    # Delete the actual file from storage
    try:
        supabase.storage.from_("files").remove([file_record.file_url])
    except Exception:
        pass  # continue even if storage cleanup fails, don't block the delete

    db.delete(file_record)
    db.commit()
    return {"message": "File permanently deleted"}