from sqlalchemy.orm import Session
from app.models.file import File
from app.models.share import Share

def get_file_with_permission(file_id: str, user_id: str, db: Session):
    """
    Returns (file, role) if the user can access the file, else (None, None).
    role is 'owner', 'editor', or 'viewer'.
    """
    file_record = db.query(File).filter(
        File.id == file_id,
        File.is_deleted == False
    ).first()

    if not file_record:
        return None, None

    if str(file_record.owner_id) == str(user_id):
        return file_record, "owner"

    share = db.query(Share).filter(
        Share.file_id == file_id,
        Share.shared_with_user_id == user_id
    ).first()

    if share:
        return file_record, share.role

    return None, None