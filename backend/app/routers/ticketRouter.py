from fastapi import APIRouter, Depends, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from dependencies.database import get_db
from schemas.ticket import TicketStatusUpdate
from schemas.ticketHistory import TicketHistoryResponse
from services.ticketService import change_ticket_status
from services.ticketHistoryService import get_ticket_history
import os
from schemas.ticketAttachment import TicketAttachmentResponse

from dependencies.auth import (
    require_admin,
    require_support_or_admin,
    require_user_or_above
)

from schemas.ticket import (
    TicketCreate,
    TicketUpdate,
    TicketAssign,
    TicketResponse,
    TicketPage,
    TicketCancel,
    TicketSurveyCreate,
    TicketReopen
)

from services.ticketService import (
    create_ticket,
    get_tickets,
    get_ticket_by_id,
    update_ticket,
    close_ticket,
    cancel_ticket,
    assign_ticket,
    upload_attachment,
    get_attachment,
    list_attachments
)

from models.user import User
from schemas.ticketComment import (
    TicketCommentCreate,
    TicketCommentResponse
)

from services.ticketCommentService import (
    create_comment,
    list_comments
)

from services.ticketFeedbackService import (
    submit_survey,
    reopen_ticket,
    get_pending_feedback
)


router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"]
)


@router.post(
    "/",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED
)
def create_new_ticket(
        ticket: TicketCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_user_or_above)
):
    return create_ticket(
        db,
        ticket,
        current_user
    )

@router.get(
    "/",
    response_model=TicketPage
)
def list_tickets(
        status: Optional[str] = None,
        priority: Optional[str] = None,
        incidencia_id: Optional[int] = None,
        subincidencia_id: Optional[int] = None,
        created_from: Optional[datetime] = None,
        created_to: Optional[datetime] = None,
        q: Optional[str] = None,
        assigned_to_me: bool = False,
        page: int = 1,
        page_size: int = 25,
        sort_by: str = "id",
        sort_desc: bool = True,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_user_or_above)
):
    return get_tickets(
        db=db,
        status=status,
        priority=priority,
        incidencia_id=incidencia_id,
        subincidencia_id=subincidencia_id,
        created_from=created_from,
        created_to=created_to,
        q=q,
        assigned_to_me=assigned_to_me,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_desc=sort_desc,
        current_user=current_user
    )


# Tickets propios que esperan confirmación o encuesta (va antes de /{ticket_id})
@router.get(
    "/pending-feedback",
    response_model=list[TicketResponse]
)
def list_pending_feedback(
        db: Session = Depends(get_db),
        current_user: User = Depends(require_user_or_above)
):
    return get_pending_feedback(db, current_user)

@router.get(
    "/{ticket_id}",
    response_model=TicketResponse
)
def get_ticket(
        ticket_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_user_or_above)
):
    return get_ticket_by_id(
        db,
        ticket_id,
        current_user
    )

@router.put(
    "/{ticket_id}",
    response_model=TicketResponse
)
def update_existing_ticket(
        ticket_id: int,
        ticket: TicketUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_support_or_admin)
):
    return update_ticket(
        db,
        ticket_id,
        ticket,
        current_user
    )

@router.patch(
    "/{ticket_id}/close",
    response_model=TicketResponse
)
def close_existing_ticket(
        ticket_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_support_or_admin)
):
    return close_ticket(
        db,
        ticket_id,
        current_user
    )


# Los tickets no se borran (auditoría). Soporte cancela cualquiera;
# el usuario solo los suyos y mientras no estén resueltos.
@router.patch(
    "/{ticket_id}/cancel",
    response_model=TicketResponse
)
def cancel_existing_ticket(
        ticket_id: int,
        data: TicketCancel,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_user_or_above)
):
    return cancel_ticket(
        db,
        ticket_id,
        data.reason,
        current_user
    )


# El solicitante confirma la solución (si está resuelto) y califica la atención
@router.post(
    "/{ticket_id}/survey",
    response_model=TicketResponse
)
def answer_ticket_survey(
        ticket_id: int,
        data: TicketSurveyCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_user_or_above)
):
    return submit_survey(
        db,
        ticket_id,
        data.rating,
        data.comment,
        current_user
    )


# El solicitante indica que el problema sigue: regresa a En progreso
@router.post(
    "/{ticket_id}/reopen",
    response_model=TicketResponse
)
def reopen_resolved_ticket(
        ticket_id: int,
        data: TicketReopen,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_user_or_above)
):
    return reopen_ticket(
        db,
        ticket_id,
        data.reason,
        current_user
    )

@router.patch(
    "/{ticket_id}/assign",
    response_model=TicketResponse
)
def assign_existing_ticket(
        ticket_id: int,
        assign_data: TicketAssign,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_support_or_admin)
):
    return assign_ticket(
        db=db,
        ticket_id=ticket_id,
        assigned_to_user_id=assign_data.assigned_to_user_id,
        current_user=current_user
    )

@router.patch(
    "/{ticket_id}/status",
    response_model=TicketResponse
)
def update_ticket_status(
        ticket_id: int,
        status: TicketStatusUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_support_or_admin)
):
    return change_ticket_status(
        db=db,
        ticket_id=ticket_id,
        status_data=status,
        current_user=current_user
    )


@router.get(
    "/{ticket_id}/history",
    response_model=list[TicketHistoryResponse]
)
def get_history(
        ticket_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_support_or_admin)
):
    return get_ticket_history(
        db=db,
        ticket_id=ticket_id
    )



@router.post(
    "/{ticket_id}/attachment",
    response_model=TicketAttachmentResponse
)
def upload_ticket_attachment(
        ticket_id: int,
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_user_or_above)
):
    return upload_attachment(
        db=db,
        ticket_id=ticket_id,
        file=file,
        current_user=current_user
    )


@router.get(
    "/{ticket_id}/attachments",
    response_model=list[TicketAttachmentResponse]
)
def list_ticket_attachments(
        ticket_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_user_or_above)
):
    return list_attachments(
        db=db,
        ticket_id=ticket_id,
        current_user=current_user
    )


@router.get("/{ticket_id}/attachments/{attachment_id}")
def download_ticket_attachment(
        ticket_id: int,
        attachment_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_user_or_above)
):
    attachment = get_attachment(
        db=db,
        ticket_id=ticket_id,
        attachment_id=attachment_id,
        current_user=current_user
    )

    return FileResponse(
        path=attachment.file_path,
        filename=attachment.original_name or os.path.basename(attachment.file_path)
    )

@router.post(
    "/{ticket_id}/comments",
    response_model=TicketCommentResponse,
    status_code=status.HTTP_201_CREATED
)
def create_ticket_comment(
        ticket_id: int,
        comment: TicketCommentCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_user_or_above)
):
    return create_comment(
        db=db,
        ticket_id=ticket_id,
        comment_data=comment,
        current_user=current_user
    )


@router.get(
    "/{ticket_id}/comments",
    response_model=list[TicketCommentResponse]
)
def list_ticket_comments(
        ticket_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_user_or_above)
):
    return list_comments(
        db=db,
        ticket_id=ticket_id,
        current_user=current_user
    )