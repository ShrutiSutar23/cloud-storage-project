from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.folder import Folder
from app.schemas.folder import FolderCreate, FolderUpdate, FolderResponse

router = APIRouter(prefix="/folders", tags=["folders"])

@router.post("", response_model=FolderResponse)
def create_folder(
    folder: FolderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # If a parent folder is given, make sure it exists and belongs to this user
    if folder.parent_folder_id:
        parent = db.query(Folder).filter(
            Folder.id == folder.parent_folder_id,
            Folder.owner_id == current_user.id
        ).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent folder not found")

    new_folder = Folder(
        name=folder.name,
        owner_id=current_user.id,
        parent_folder_id=folder.parent_folder_id
    )
    db.add(new_folder)
    db.commit()
    db.refresh(new_folder)
    return new_folder


@router.get("", response_model=list[FolderResponse])
def list_folders(
    parent_folder_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Folder).filter(Folder.owner_id == current_user.id)
    if parent_folder_id:
        query = query.filter(Folder.parent_folder_id == parent_folder_id)
    else:
        query = query.filter(Folder.parent_folder_id.is_(None))
    return query.all()


@router.get("/{folder_id}", response_model=FolderResponse)
def get_folder(
    folder_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    folder = db.query(Folder).filter(
        Folder.id == folder_id,
        Folder.owner_id == current_user.id
    ).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    return folder


@router.put("/{folder_id}", response_model=FolderResponse)
def rename_folder(
    folder_id: str,
    update: FolderUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    folder = db.query(Folder).filter(
        Folder.id == folder_id,
        Folder.owner_id == current_user.id
    ).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    folder.name = update.name
    db.commit()
    db.refresh(folder)
    return folder


@router.delete("/{folder_id}")
def delete_folder(
    folder_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    folder = db.query(Folder).filter(
        Folder.id == folder_id,
        Folder.owner_id == current_user.id
    ).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    db.delete(folder)
    db.commit()
    return {"message": "Folder deleted"}


@router.get("/{folder_id}/breadcrumb")
def get_breadcrumb(
    folder_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Walks up the parent chain to build the folder path, e.g. Home > Docs > 2024"""
    path = []
    current_id = folder_id

    while current_id:
        folder = db.query(Folder).filter(
            Folder.id == current_id,
            Folder.owner_id == current_user.id
        ).first()
        if not folder:
            break
        path.insert(0, {"id": str(folder.id), "name": folder.name})
        current_id = folder.parent_folder_id

    return {"breadcrumb": path}