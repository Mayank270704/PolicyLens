from __future__ import annotations

import math
from typing import TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.schemas.common import PaginatedResponse

T = TypeVar("T")


def paginate(db: Session, stmt, page: int, page_size: int, model_cls, out_cls) -> PaginatedResponse:
    """Applies LIMIT/OFFSET to a SQLAlchemy select() statement and wraps
    the result in a PaginatedResponse. `stmt` must already have any
    filters/ordering applied; this only adds counting + windowing."""
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.execute(count_stmt).scalar_one()

    windowed = stmt.limit(page_size).offset((page - 1) * page_size)
    rows = db.execute(windowed).scalars().all()

    total_pages = max(1, math.ceil(total / page_size)) if page_size else 1
    return PaginatedResponse(
        items=[out_cls.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
