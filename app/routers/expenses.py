from fastapi import APIRouter, HTTPException, status, Depends, Query, Request
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal
from app.models import ExpenseCreate, ExpenseUpdate, Expense
from app.auth import get_current_user
from app.database import supabase
from app.ai_categorizer import categorizer

router = APIRouter()

@router.post("/", response_model=Expense, status_code=status.HTTP_201_CREATED)
async def create_expense(request: Request, expense_data: ExpenseCreate, current_user = Depends(get_current_user)):
    """Create a new expense with AI categorization"""
    try:
        # Log raw request body first
        body = await request.body()
        print(f"🔍 Raw request body: {body.decode()}")
        
        user_id = current_user['id']
        
        print(f"💰 Backend received expense data:")
        print(f"   - amount: {expense_data.amount}")
        print(f"   - note: '{expense_data.note}'")
        print(f"   - date: {expense_data.date} (type: {type(expense_data.date)})")
        print(f"   - category_id: {expense_data.category_id}")
        
        # Auto-categorize if no category provided
        category_id = expense_data.category_id
        print(f"🔍 Expense creation - Initial category_id: {category_id}")
        print(f"🔍 Expense note: '{expense_data.note}'")
        
        if not category_id:
            print(f"🤖 Starting AI categorization for note: '{expense_data.note}'")
            category_id = categorizer.categorize_expense(expense_data.note, user_id)
            print(f"🎯 AI categorization result: {category_id}")
            
            if not category_id:
                print("⚠️ AI categorization failed, falling back to 'Other' category")
                # Fallback to "Other" category
                other_cat = supabase.table('categories').select('id').eq('user_id', user_id).eq('name', 'Other').execute()
                if other_cat.data:
                    category_id = other_cat.data[0]['id']
                    print(f"✅ Using 'Other' category: {category_id}")
                else:
                    print("❌ No 'Other' category found!")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="No suitable category found and no Other category exists"
                    )
            else:
                print(f"✅ AI categorization successful: {category_id}")
        
        # Verify category belongs to user
        cat_result = supabase.table('categories').select('*').eq('id', category_id).eq('user_id', user_id).execute()
        if not cat_result.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category not found or doesn't belong to user"
            )
        
        # Create expense
        expense_dict = {
            "user_id": user_id,
            "amount": float(expense_data.amount),
            "note": expense_data.note,
            "date": (expense_data.date or date.today()).isoformat(),
            "category_id": category_id
        }
        print(expense_dict)
        result = supabase.table('expenses').insert(expense_dict).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create expense"
            )
        
        expense = result.data[0]
        category = cat_result.data[0]
        
        response_data = {
            "id": expense['id'],
            "user_id": expense['user_id'],
            "amount": Decimal(str(expense['amount'])),
            "note": expense['note'],
            "date": datetime.fromisoformat(expense['date']).date(),
            "category_id": expense['category_id'],
            "category_name": category['name'],
            "created_at": datetime.fromisoformat(expense['created_at'].replace('Z', '+00:00')),
            "updated_at": datetime.fromisoformat(expense['updated_at'].replace('Z', '+00:00'))
        }
        
        print(f"📤 Expense created successfully:")
        print(f"   - ID: {response_data['id']}")
        print(f"   - Note: '{response_data['note']}'")
        print(f"   - Category ID: {response_data['category_id']}")
        print(f"   - Category Name: {response_data['category_name']}")
        print(f"   - Amount: {response_data['amount']}")
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Create expense error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create expense: {str(e)}"
        )

@router.get("/", response_model=List[Expense])
async def get_expenses(
    current_user = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category_id: Optional[str] = None,
    search: Optional[str] = None
):
    """Get user's expenses with filtering and pagination"""
    try:
        user_id = current_user['id']
        
        # Build query
        query = supabase.table('expenses').select(
            'id, amount, note, date, category_id, created_at, updated_at, categories(name)'
        ).eq('user_id', user_id)
        
        # Apply filters
        if start_date:
            query = query.gte('date', start_date.isoformat())
        if end_date:
            query = query.lte('date', end_date.isoformat())
        if category_id:
            query = query.eq('category_id', category_id)
        if search:
            query = query.ilike('note', f'%{search}%')
        
        # Apply pagination and ordering
        query = query.order('date', desc=True).order('created_at', desc=True)
        query = query.range(offset, offset + limit - 1)
        
        result = query.execute()
        
        expenses = []
        for expense in result.data:
            expenses.append({
                "id": expense['id'],
                "user_id": user_id,
                "amount": Decimal(str(expense['amount'])),
                "note": expense['note'],
                "date": datetime.fromisoformat(expense['date']).date(),
                "category_id": expense['category_id'],
                "category_name": expense['categories']['name'] if expense['categories'] else 'Unknown',
                "created_at": datetime.fromisoformat(expense['created_at'].replace('Z', '+00:00')),
                "updated_at": datetime.fromisoformat(expense['updated_at'].replace('Z', '+00:00'))
            })
        
        return expenses
        
    except Exception as e:
        print(f"❌ Get expenses error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch expenses: {str(e)}"
        )

@router.get("/{expense_id}", response_model=Expense)
async def get_expense(expense_id: str, current_user = Depends(get_current_user)):
    """Get a specific expense"""
    try:
        user_id = current_user['id']
        
        result = supabase.table('expenses').select(
            'id, amount, note, date, category_id, created_at, updated_at, categories(name)'
        ).eq('id', expense_id).eq('user_id', user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found"
            )
        
        expense = result.data[0]
        
        return {
            "id": expense['id'],
            "user_id": user_id,
            "amount": Decimal(str(expense['amount'])),
            "note": expense['note'],
            "date": datetime.fromisoformat(expense['date']).date(),
            "category_id": expense['category_id'],
            "category_name": expense['categories']['name'] if expense['categories'] else 'Unknown',
            "created_at": datetime.fromisoformat(expense['created_at'].replace('Z', '+00:00')),
            "updated_at": datetime.fromisoformat(expense['updated_at'].replace('Z', '+00:00'))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Get expense error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch expense: {str(e)}"
        )

@router.put("/{expense_id}", response_model=Expense)
async def update_expense(
    expense_id: str, 
    expense_data: ExpenseUpdate, 
    current_user = Depends(get_current_user)
):
    """Update an expense"""
    try:
        user_id = current_user['id']
        
        # Check if expense exists and belongs to user
        existing = supabase.table('expenses').select('*').eq('id', expense_id).eq('user_id', user_id).execute()
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found"
            )
        
        # Build update data
        update_data = {}
        if expense_data.amount is not None:
            update_data['amount'] = float(expense_data.amount)
        if expense_data.note is not None:
            update_data['note'] = expense_data.note
            # Re-categorize if note changed and no explicit category provided
            if expense_data.category_id is None:
                new_category_id = categorizer.categorize_expense(expense_data.note, user_id)
                if new_category_id:
                    update_data['category_id'] = new_category_id
        if expense_data.date is not None:
            update_data['date'] = expense_data.date.isoformat()
        if expense_data.category_id is not None:
            # Verify category belongs to user
            cat_result = supabase.table('categories').select('id').eq('id', expense_data.category_id).eq('user_id', user_id).execute()
            if not cat_result.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Category not found or doesn't belong to user"
                )
            update_data['category_id'] = expense_data.category_id
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No data provided for update"
            )
        
        update_data['updated_at'] = datetime.utcnow().isoformat()
        
        # Update expense
        result = supabase.table('expenses').update(update_data).eq('id', expense_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update expense"
            )
        
        # Get updated expense with category name
        updated_result = supabase.table('expenses').select(
            'id, amount, note, date, category_id, created_at, updated_at, categories(name)'
        ).eq('id', expense_id).execute()
        
        expense = updated_result.data[0]
        
        return {
            "id": expense['id'],
            "user_id": user_id,
            "amount": Decimal(str(expense['amount'])),
            "note": expense['note'],
            "date": datetime.fromisoformat(expense['date']).date(),
            "category_id": expense['category_id'],
            "category_name": expense['categories']['name'] if expense['categories'] else 'Unknown',
            "created_at": datetime.fromisoformat(expense['created_at'].replace('Z', '+00:00')),
            "updated_at": datetime.fromisoformat(expense['updated_at'].replace('Z', '+00:00'))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Update expense error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update expense: {str(e)}"
        )

@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(expense_id: str, current_user = Depends(get_current_user)):
    """Delete an expense"""
    try:
        user_id = current_user['id']
        
        # Check if expense exists and belongs to user
        existing = supabase.table('expenses').select('id').eq('id', expense_id).eq('user_id', user_id).execute()
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found"
            )
        
        # Delete expense
        result = supabase.table('expenses').delete().eq('id', expense_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete expense"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Delete expense error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete expense: {str(e)}"
        )

@router.post("/categorize-preview")
async def preview_categorization(note: str, current_user = Depends(get_current_user)):
    """Preview expense categorization for a given note using Claude AI"""
    try:
        user_id = current_user['id']
        print(f"🔍 Preview categorization request for note: '{note}' from user: {user_id}")
        category_id = categorizer.categorize_expense(note, user_id)
        print(f"🎯 Preview categorization result: {category_id}")
        
        if category_id:
            cat_result = supabase.table('categories').select('name, emoji').eq('id', category_id).execute()
            if cat_result.data:
                category = cat_result.data[0]
                print(f"🔍 Preview categorization: {category['name']} ({category_id})")
                return {
                    "category_id": category_id,
                    "category_name": category['name'],
                    "emoji": category.get('emoji'),
                    "suggestions": categorizer.get_category_suggestions_with_openai(note),
                    "ai_powered": True
                }
        
        return {
            "category_id": None,
            "category_name": "Other",
            "emoji": "📝",
            "suggestions": categorizer.get_category_suggestions_with_openai(note),
            "ai_powered": True
        }
        
    except Exception as e:
        print(f"❌ Preview categorization error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to preview categorization: {str(e)}"
        )