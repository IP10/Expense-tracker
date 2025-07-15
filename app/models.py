from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal

class UserRegister(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (min 8 characters)")
    full_name: str = Field(..., min_length=2, description="User full name")

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
    amount: Decimal = Field(..., gt=0, description="Expense amount in INR (must be positive)")
    note: str = Field(..., max_length=500, description="Expense description/note")
    date: date = Field(default_factory=date.today, description="Expense date")
    category_id: Optional[str] = Field(None, description="Manual category override")

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        if v > Decimal('10000000'):  # 1 crore limit
            raise ValueError('Amount cannot exceed ₹1,00,00,000')
        return round(v, 2)

    @field_validator('note')
    @classmethod
    def validate_note(cls, v):
        if not v.strip():
            raise ValueError('Note cannot be empty')
        return v.strip()

class ExpenseUpdate(BaseModel):
    amount: Optional[Decimal] = Field(None, gt=0)
    note: Optional[str] = Field(None, max_length=500)
    date: Optional[date] = None
    category_id: Optional[str] = None

    @field_validator('amount')
    @classmethod
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
    name: str = Field(..., min_length=1, max_length=50)
    emoji: Optional[str] = Field(None, description="Category emoji")
    is_system: bool = Field(default=False, description="System-defined category")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        return v.strip().title()

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
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

    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v, info):
        if info.data.get('start_date') and v < info.data['start_date']:
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