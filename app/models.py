from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal

class UserRegister(BaseModel):
    email: str
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str
    expires_in: int

class User(BaseModel):
    id: str
    email: str
    full_name: str
    created_at: datetime
    updated_at: datetime

class ExpenseCreate(BaseModel):
    amount: Decimal
    note: str
    date: Optional[date] = None
    category_id: Optional[str] = None

    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        if v > Decimal('10000000'):  # 1 crore limit
            raise ValueError('Amount cannot exceed ₹1,00,00,000')
        return round(v, 2)

    @validator('note')
    def validate_note(cls, v):
        if not v.strip():
            raise ValueError('Note cannot be empty')
        return v.strip()

class ExpenseUpdate(BaseModel):
    amount: Optional[Decimal] = None
    note: Optional[str] = None
    date: Optional[date] = None
    category_id: Optional[str] = None

    @validator('amount')
    def validate_amount(cls, v):
        if v is not None:
            if v <= 0:
                raise ValueError('Amount must be positive')
            if v > Decimal('10000000'):
                raise ValueError('Amount cannot exceed ₹1,00,00,000')
            return round(v, 2)
        return v

class Expense(BaseModel):
    id: str
    user_id: str
    amount: Decimal
    note: str
    date: date
    category_id: str
    category_name: str
    created_at: datetime
    updated_at: datetime

class CategoryCreate(BaseModel):
    name: str
    emoji: Optional[str] = None
    is_system: bool = False

    @validator('name')
    def validate_name(cls, v):
        return v.strip().title()

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    emoji: Optional[str] = None

class Category(BaseModel):
    id: str
    name: str
    emoji: Optional[str]
    is_system: bool
    user_id: Optional[str]
    created_at: datetime
    updated_at: datetime

class ReportRequest(BaseModel):
    start_date: date
    end_date: date

    @validator('end_date')
    def validate_date_range(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('End date must be after start date')
        return v

class CategoryReport(BaseModel):
    category_id: str
    category_name: str
    total_amount: Decimal
    transaction_count: int
    percentage: float

class ExpenseReport(BaseModel):
    total_amount: Decimal
    transaction_count: int
    categories: List[CategoryReport]
    start_date: date
    end_date: date

class MonthlyTrend(BaseModel):
    month: str
    year: int
    total_amount: Decimal
    transaction_count: int