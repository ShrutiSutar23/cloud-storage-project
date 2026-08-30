import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.permissions import get_file_with_permission
from app.models.user import User
from app.models.share import Share
from app.models.link_share import LinkShare
from app.schemas.share import ShareCreate, ShareResponse, LinkShareCreate, LinkShareResponse

router = APIRouter(tags=["sharing"])

@router.post("/shares", response_model=ShareResponse)
def create_share(
    share: ShareCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file_record, role = get_file_with_permission(str(share.file_id), str(current_user.id), db)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    if role != "owner":
        raise HTTPException(status_code=403, detail="Only the owner can share this file")

    target_user = db.query(User).filter(User.email == share.shared_with_email).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="No user found with that email")

    existing = db.query(Share).filter(
        Share.file_id == share.file_id,
        Share.shared_with_user_id == target_user.id
    ).first()
    if existing:
        existing.role = share.role
        db.commit()
        db.refresh(existing)
        return existing

    new_share = Share(
        file_id=share.file_id,
        shared_with_user_id=target_user.id,
        role=share.role
    )
    db.add(new_share)
    db.commit()
    db.refresh(new_share)
    return new_share


@router.get("/shares/file/{file_id}", response_model=list[ShareResponse])
def list_shares_for_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file_record, role = get_file_with_permission(file_id, str(current_user.id), db)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    if role != "owner":
        raise HTTPException(status_code=403, detail="Only the owner can view sharing info")

    return db.query(Share).filter(Share.file_id == file_id).all()


@router.delete("/shares/{share_id}")
def revoke_share(
    share_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    share = db.query(Share).filter(Share.id == share_id).first()
    if not share:
        raise HTTPException(status_code=404, detail="Share not found")

    file_record, role = get_file_with_permission(str(share.file_id), str(current_user.id), db)
    if not file_record or role != "owner":
        raise HTTPException(status_code=403, detail="Only the owner can revoke sharing")

    db.delete(share)
    db.commit()
    return {"message": "Share revoked"}


@router.post("/public-link", response_model=LinkShareResponse)
def create_public_link(
    link: LinkShareCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file_record, role = get_file_with_permission(str(link.file_id), str(current_user.id), db)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    if role != "owner":
        raise HTTPException(status_code=403, detail="Only the owner can create a public link")

    token = secrets.token_urlsafe(16)
    expires_at = None
    if link.expires_in_hours:
        expires_at = datetime.utcnow() + timedelta(hours=link.expires_in_hours)

    new_link = LinkShare(
        file_id=link.file_id,
        token=token,
        expires_at=expires_at,
        password=link.password
    )
    db.add(new_link)
    db.commit()
    db.refresh(new_link)
    return new_link


@router.get("/public-link/{token}")
def access_public_link(token: str, password: str = None, db: Session = Depends(get_db)):
    from app.core.supabase_client import supabase
    from app.models.file import File

    link = db.query(LinkShare).filter(LinkShare.token == token).first()
    if not link:
        raise HTTPException(status_code=404, detail="Invalid link")

    if link.expires_at and link.expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="This link has expired")

    if link.password and link.password != password:
        raise HTTPException(status_code=401, detail="Incorrect password")

    file_record = db.query(File).filter(File.id == link.file_id, File.is_deleted == False).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    signed_url = supabase.storage.from_("files").create_signed_url(file_record.file_url, 3600)

    return {
        "name": file_record.name,
        "size": file_record.size,
        "download_url": signed_url.get("signedURL")
    }