from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
from datetime import datetime, timezone
 

app = FastAPI()
 
tickets_db = [
    {"id": 1, "movie_name": "Doctor Strange 3", "room_code": "IMAX-01", "quantity": 2, "status": "confirmed", "created_at": "2026-07-01T19:00:00Z"},
    {"id": 2, "movie_name": "Avatar 3", "room_code": "PREMIUM-02", "quantity": 1, "status": "confirmed", "created_at": "2026-07-01T20:15:00Z"}
]
 

next_id = len(tickets_db)
 

class TicketCreate(BaseModel):
    movie_name: str = Field(..., min_length=1, description="Tên phim, không được để trống")
    room_code: str = Field(..., min_length=1, description="Mã phòng chiếu, không được để trống")
    quantity: int = Field(..., ge=1, le=10, description="Số lượng vé, từ 1 đến 10")

def build_envelope(status_code: int, message: str, data, error, path: str):
    return {
        "statusCode": status_code,
        "message": message,
        "data": data,
        "error": error,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "path": path,
    }
 

@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict):
        message = detail.get("message", "Đã có lỗi xảy ra")
        error = detail.get("error", str(exc.detail))
    else:
        message = str(detail)
        error = str(detail)
 
    envelope = build_envelope(
        status_code=exc.status_code,
        message=message,
        data=None,
        error=error,
        path=str(request.url.path),
    )
    return JSONResponse(status_code=exc.status_code, content=envelope)
 
 

@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError):
    envelope = build_envelope(
        status_code=422,
        message="Dữ liệu đầu vào không hợp lệ!",
        data=None,
        error=exc.errors(),
        path=str(request.url.path),
    )
    return JSONResponse(status_code=422, content=envelope)
 

@app.get("/tickets", status_code=status.HTTP_200_OK)
def get_tickets(request: Request):
    return build_envelope(
        status_code=200,
        message="Lấy danh sách vé thành công!",
        data=tickets_db,
        error=None,
        path=str(request.url.path),
    )
 
 
app.post("/tickets", status_code=status.HTTP_201_CREATED)
def create_ticket(ticket: TicketCreate, request: Request):
    global next_id

    for i in tickets_db:
        if i["movie_name"] == ticket.movie_name and i["room_code"] == ticket.room_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Lỗi: Vé xem phim tại phòng chiếu này đã được đặt!",
                    "error": "ERR-CINE-01: Ticket conflict for movie and room combination.",
                },
            )
 
    new_ticket = {
        "id": next_id,
        "movie_name": ticket.movie_name,
        "room_code": ticket.room_code,
        "quantity": ticket.quantity,
        "status": "confirmed",
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    tickets_db.append(new_ticket)
    next_id += 1
 
    return build_envelope(
        status_code=201,
        message="Đặt vé thành công!",
        data=new_ticket,
        error=None,
        path=str(request.url.path),
    )
 
 
@app.delete("/tickets/{ticket_id}", status_code=status.HTTP_200_OK)
def delete_ticket(ticket_id: int, request: Request):
    for index, i in enumerate(tickets_db):
        if i["id"] == ticket_id:
            tickets_db.pop(index)
            return build_envelope(
                status_code=200,
                message="Hủy vé thành công!",
                data=None,
                error=None,
                path=str(request.url.path),
            )
 
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "message": "Lỗi: Không tìm thấy mã vé yêu cầu!",
            "error": "ERR-CINE-02: Ticket ID does not exist.",
        },
    )
 