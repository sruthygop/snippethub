from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from database import get_db
from models import Snippet, Tag, User
from routers.auth import get_current_user
from schemas import SnippetCreate, SnippetOut, SnippetUpdate

router = APIRouter(prefix="/snippets", tags=["snippets"])


def get_own_snippet(snippet_id: int, user: User, db: Session) -> Snippet:
    snippet = db.get(Snippet, snippet_id)
    if not snippet or snippet.user_id != user.id:
        raise HTTPException(status_code=404, detail="Snippet not found")
    return snippet


def get_or_create_tags(names: list[str], db: Session) -> list[Tag]:
    # Clean the names: remove spaces, make lowercase, remove duplicates
    clean = {n.strip().lower() for n in names if n.strip()}
    tags = []
    for name in sorted(clean):
        if len(name) > 50:
            raise HTTPException(status_code=400, detail="Tag is too long (max 50)")
        tag = db.query(Tag).filter(Tag.name == name).first()
        if not tag:
            tag = Tag(name=name)
            db.add(tag)
        tags.append(tag)
    return tags


@router.post("", response_model=SnippetOut, status_code=201)
def create_snippet(
    data: SnippetCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    snippet = Snippet(**data.model_dump(exclude={"tags"}), user_id=user.id)
    snippet.tags = get_or_create_tags(data.tags, db)
    db.add(snippet)
    db.commit()
    db.refresh(snippet)
    return snippet


@router.get("", response_model=list[SnippetOut])
def list_snippets(
    q: Optional[str] = Query(None, description="Search text"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(Snippet).filter(Snippet.user_id == user.id)

    if tag:
        query = query.filter(Snippet.tags.any(Tag.name == tag.strip().lower()))

    if q:
        document = func.to_tsvector(
            "english",
            Snippet.title + " " + func.coalesce(Snippet.description, "") + " " + Snippet.code,
        )
        query = query.filter(
            or_(
                document.op("@@")(func.plainto_tsquery("english", q)),
                Snippet.title.ilike(f"%{q}%"),
            )
        )

    return query.order_by(Snippet.created_at.desc()).all()


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
    changes = data.model_dump(exclude_unset=True)
    tag_names = changes.pop("tags", None)

    for field, value in changes.items():
        setattr(snippet, field, value)
    if tag_names is not None:
        snippet.tags = get_or_create_tags(tag_names, db)
    snippet.updated_at = func.now()
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