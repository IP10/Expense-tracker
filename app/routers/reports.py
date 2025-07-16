from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List
from datetime import date, datetime, timedelta
from decimal import Decimal
from calendar import monthrange
from app.models import ReportRequest, ExpenseReport, CategoryReport, MonthlyTrend
from app.auth import get_current_user
from app.database import supabase

router = APIRouter()

@router.post("/", response_model=ExpenseReport)
async def generate_report(report_request: ReportRequest, current_user = Depends(get_current_user)):
    """Generate expense report for a date range"""
    try:
        user_id = current_user['id']
        
        return await _generate_report_data(
            user_id, 
            report_request.start_date, 
            report_request.end_date
        )
        
    except Exception as e:
        print(f"❌ Generate report error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}"
        )

@router.get("/this-month", response_model=ExpenseReport)
async def get_this_month_report(current_user = Depends(get_current_user)):
    """Get report for current month"""
    try:
        user_id = current_user['id']
        today = date.today()
        start_date = date(today.year, today.month, 1)
        end_date = date(today.year, today.month, monthrange(today.year, today.month)[1])
        
        return await _generate_report_data(user_id, start_date, end_date)
        
    except Exception as e:
        print(f"❌ This month report error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate this month report: {str(e)}"
        )

@router.get("/last-month", response_model=ExpenseReport)
async def get_last_month_report(current_user = Depends(get_current_user)):
    """Get report for last month"""
    try:
        user_id = current_user['id']
        today = date.today()
        
        # Calculate last month
        if today.month == 1:
            last_month = 12
            last_year = today.year - 1
        else:
            last_month = today.month - 1
            last_year = today.year
        
        start_date = date(last_year, last_month, 1)
        end_date = date(last_year, last_month, monthrange(last_year, last_month)[1])
        
        return await _generate_report_data(user_id, start_date, end_date)
        
    except Exception as e:
        print(f"❌ Last month report error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate last month report: {str(e)}"
        )

@router.get("/last-n-months/{months}", response_model=ExpenseReport)
async def get_last_n_months_report(months: int, current_user = Depends(get_current_user)):
    """Get report for last N months"""
    try:
        if months < 1 or months > 12:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Months must be between 1 and 12"
            )
        
        user_id = current_user['id']
        today = date.today()
        
        # Calculate start date (N months back)
        start_date = today - timedelta(days=months * 30)  # Approximate
        start_date = date(start_date.year, start_date.month, 1)
        
        # End date is end of current month
        end_date = date(today.year, today.month, monthrange(today.year, today.month)[1])
        
        return await _generate_report_data(user_id, start_date, end_date)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Last N months report error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate last {months} months report: {str(e)}"
        )

@router.get("/monthly-trend", response_model=List[MonthlyTrend])
async def get_monthly_trend(
    current_user = Depends(get_current_user),
    months: int = Query(6, ge=1, le=12, description="Number of months to include in trend")
):
    """Get monthly spending trend"""
    try:
        user_id = current_user['id']
        today = date.today()
        
        trends = []
        
        for i in range(months):
            # Calculate month and year
            month_offset = today.month - i - 1
            year = today.year
            month = month_offset
            
            if month <= 0:
                month += 12
                year -= 1
            
            # Get first and last day of the month
            start_date = date(year, month, 1)
            end_date = date(year, month, monthrange(year, month)[1])
            
            # Query expenses for this month
            result = supabase.table('expenses').select(
                'amount'
            ).eq('user_id', user_id).gte(
                'date', start_date.isoformat()
            ).lte(
                'date', end_date.isoformat()
            ).execute()
            
            total_amount = Decimal('0')
            transaction_count = len(result.data)
            
            for expense in result.data:
                total_amount += Decimal(str(expense['amount']))
            
            trends.append({
                "month": start_date.strftime("%B"),
                "year": year,
                "total_amount": total_amount,
                "transaction_count": transaction_count
            })
        
        # Reverse to show oldest to newest
        trends.reverse()
        return trends
        
    except Exception as e:
        print(f"❌ Monthly trend error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate monthly trend: {str(e)}"
        )

@router.get("/summary")
async def get_expense_summary(current_user = Depends(get_current_user)):
    """Get overall expense summary"""
    try:
        user_id = current_user['id']
        
        # Get total expenses
        total_result = supabase.table('expenses').select(
            'amount'
        ).eq('user_id', user_id).execute()
        
        total_amount = Decimal('0')
        total_count = len(total_result.data)
        
        for expense in total_result.data:
            total_amount += Decimal(str(expense['amount']))
        
        # Get this month's expenses
        today = date.today()
        start_of_month = date(today.year, today.month, 1)
        
        this_month_result = supabase.table('expenses').select(
            'amount'
        ).eq('user_id', user_id).gte(
            'date', start_of_month.isoformat()
        ).execute()
        
        this_month_amount = Decimal('0')
        this_month_count = len(this_month_result.data)
        
        for expense in this_month_result.data:
            this_month_amount += Decimal(str(expense['amount']))
        
        # Get last month's expenses for comparison
        if today.month == 1:
            last_month = 12
            last_year = today.year - 1
        else:
            last_month = today.month - 1
            last_year = today.year
        
        last_month_start = date(last_year, last_month, 1)
        last_month_end = date(last_year, last_month, monthrange(last_year, last_month)[1])
        
        last_month_result = supabase.table('expenses').select(
            'amount'
        ).eq('user_id', user_id).gte(
            'date', last_month_start.isoformat()
        ).lte(
            'date', last_month_end.isoformat()
        ).execute()
        
        last_month_amount = Decimal('0')
        for expense in last_month_result.data:
            last_month_amount += Decimal(str(expense['amount']))
        
        # Calculate percentage change
        percentage_change = 0.0
        if last_month_amount > 0:
            percentage_change = float(
                ((this_month_amount - last_month_amount) / last_month_amount) * 100
            )
        
        return {
            "total_amount": total_amount,
            "total_transactions": total_count,
            "this_month_amount": this_month_amount,
            "this_month_transactions": this_month_count,
            "last_month_amount": last_month_amount,
            "percentage_change": round(percentage_change, 2),
            "average_per_transaction": round(total_amount / total_count, 2) if total_count > 0 else 0
        }
        
    except Exception as e:
        print(f"❌ Summary report error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary: {str(e)}"
        )

async def _generate_report_data(user_id: str, start_date: date, end_date: date) -> ExpenseReport:
    """Helper function to generate report data"""
    
    # Get expenses with categories for the date range
    result = supabase.table('expenses').select(
        'amount, category_id, categories(name)'
    ).eq('user_id', user_id).gte(
        'date', start_date.isoformat()
    ).lte(
        'date', end_date.isoformat()
    ).execute()
    
    # Calculate totals and group by category
    total_amount = Decimal('0')
    category_totals = {}
    category_counts = {}
    category_names = {}
    
    for expense in result.data:
        amount = Decimal(str(expense['amount']))
        category_id = expense['category_id']
        category_name = expense['categories']['name'] if expense['categories'] else 'Unknown'
        
        total_amount += amount
        
        if category_id not in category_totals:
            category_totals[category_id] = Decimal('0')
            category_counts[category_id] = 0
            category_names[category_id] = category_name
        
        category_totals[category_id] += amount
        category_counts[category_id] += 1
    
    # Calculate percentages and create category reports
    categories = []
    for category_id, amount in category_totals.items():
        percentage = float((amount / total_amount) * 100) if total_amount > 0 else 0
        
        categories.append({
            "category_id": category_id,
            "category_name": category_names[category_id],
            "total_amount": amount,
            "transaction_count": category_counts[category_id],
            "percentage": round(percentage, 2)
        })
    
    # Sort categories by amount (descending)
    categories.sort(key=lambda x: x["total_amount"], reverse=True)
    
    return {
        "total_amount": total_amount,
        "transaction_count": len(result.data),
        "categories": categories,
        "start_date": start_date,
        "end_date": end_date
    }