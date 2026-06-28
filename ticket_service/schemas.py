from pydantic import BaseModel

class CreateTicketRequest(BaseModel):
    user_id: str

class TicketResponse(BaseModel):
    ticket_id: str
    status: str
    user_id: str

class DeleteResponse(BaseModel):
    message: str