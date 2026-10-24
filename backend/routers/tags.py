from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Snippet, Tag, User, snippet_tags
from routers.auth import get_current_user
from schemas import TagOut

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=list[TagOut])
def list_tags(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Only the tags used on this user's own snippets
    return (
        db.query(Tag)
        .join(snippet_tags, snippet_tags.c.tag_id == Tag.id)
        .join(Snippet, Snippet.id == snippet_tags.c.snippet_id)
        .filter(Snippet.user_id == user.id)
        .distinct()
        .order_by(Tag.name)
        .all()
    )