from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Snippet, User
from routers.auth import get_current_user
from schemas import SnippetCreate, SnippetOut, SnippetUpdate

router = APIRouter(prefix="/snippets", tags=["snippets"])


def get_own_snippet(snippet_id: int, user: User, db: Session) -> Snippet:
    snippet = db.get(Snippet, snippet_id)
    if not snippet or snippet.user_id != user.id:
        raise HTTPException(status_code=404, detail="Snippet not found")
    return snippet


@router.post("", response_model=SnippetOut, status_code=201)
def create_snippet(
    data: SnippetCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    snippet = Snippet(**data.model_dump(), user_id=user.id)
    db.add(snippet)
    db.commit()
    db.refresh(snippet)
    return snippet


@router.get("", response_model=list[SnippetOut])
def list_snippets(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return (
        db.query(Snippet)
        .filter(Snippet.user_id == user.id)
        .order_by(Snippet.created_at.desc())
        .all()
    )


@router.get("/{snippet_id}", response_model=SnippetOut)
def get_snippet(
    snippet_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return get_own_snippet(snippet_id, user, db)


@router.put("/{snippet_id}", response_model=SnippetOut)
def update_snippet(
    snippet_id: int,
    data: SnippetUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    snippet = get_own_snippet(snippet_id, user, db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(snippet, field, value)
    db.commit()
    db.refresh(snippet)
    return snippet


@router.delete("/{snippet_id}", status_code=204)
def delete_snippet(
    snippet_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    snippet = get_own_snippet(snippet_id, user, db)
    db.delete(snippet)
    db.commit()