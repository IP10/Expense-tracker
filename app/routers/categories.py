from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from app.models import CategoryCreate, CategoryUpdate, Category
from app.auth import get_current_user
from app.database import supabase

router = APIRouter()

@router.get("/", response_model=List[Category])
async def get_categories(current_user = Depends(get_current_user)):
    """Get all categories for the current user"""
    try:
        user_id = current_user['id']
        
        result = supabase.table('categories').select('*').eq('user_id', user_id).order('name').execute()
        
        categories = []
        for cat in result.data:
            categories.append({
                "id": cat['id'],
                "name": cat['name'],
                "emoji": cat.get('emoji'),
                "is_system": cat.get('is_system', False),
                "user_id": cat['user_id'],
                "created_at": cat['created_at'],
                "updated_at": cat['updated_at']
            })
        
        return categories
        
    except Exception as e:
        print(f"❌ Get categories error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch categories: {str(e)}"
        )

@router.post("/", response_model=Category, status_code=status.HTTP_201_CREATED)
async def create_category(category_data: CategoryCreate, current_user = Depends(get_current_user)):
    """Create a new category"""
    try:
        user_id = current_user['id']
        
        # Check if category name already exists for user
        existing = supabase.table('categories').select('id').eq('user_id', user_id).eq('name', category_data.name).execute()
        if existing.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category with this name already exists"
            )
        
        # Create category
        category_dict = {
            "name": category_data.name,
            "emoji": category_data.emoji,
            "is_system": category_data.is_system,
            "user_id": user_id
        }
        
        result = supabase.table('categories').insert(category_dict).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create category"
            )
        
        category = result.data[0]
        
        return {
            "id": category['id'],
            "name": category['name'],
            "emoji": category.get('emoji'),
            "is_system": category.get('is_system', False),
            "user_id": category['user_id'],
            "created_at": category['created_at'],
            "updated_at": category['updated_at']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Create category error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create category: {str(e)}"
        )

@router.put("/{category_id}", response_model=Category)
async def update_category(
    category_id: str,
    category_data: CategoryUpdate,
    current_user = Depends(get_current_user)
):
    """Update a category"""
    try:
        user_id = current_user['id']
        
        # Check if category exists and belongs to user
        existing = supabase.table('categories').select('*').eq('id', category_id).eq('user_id', user_id).execute()
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        category = existing.data[0]
        
        # Build update data
        update_data = {}
        if category_data.name is not None:
            # Check if new name conflicts with existing categories
            name_check = supabase.table('categories').select('id').eq('user_id', user_id).eq('name', category_data.name).neq('id', category_id).execute()
            if name_check.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Category with this name already exists"
                )
            update_data['name'] = category_data.name
        
        if category_data.emoji is not None:
            update_data['emoji'] = category_data.emoji
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No data provided for update"
            )
        
        update_data['updated_at'] = 'now()'
        
        # Update category
        result = supabase.table('categories').update(update_data).eq('id', category_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update category"
            )
        
        updated_category = result.data[0]
        
        return {
            "id": updated_category['id'],
            "name": updated_category['name'],
            "emoji": updated_category.get('emoji'),
            "is_system": updated_category.get('is_system', False),
            "user_id": updated_category['user_id'],
            "created_at": updated_category['created_at'],
            "updated_at": updated_category['updated_at']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Update category error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update category: {str(e)}"
        )

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: str, current_user = Depends(get_current_user)):
    """Delete a category (moves expenses to 'Other' category)"""
    try:
        user_id = current_user['id']
        
        # Check if category exists and belongs to user
        existing = supabase.table('categories').select('*').eq('id', category_id).eq('user_id', user_id).execute()
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        category = existing.data[0]
        
        # Prevent deletion of "Other" category
        if category['name'] == 'Other':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete 'Other' category"
            )
        
        # Get "Other" category ID
        other_category = supabase.table('categories').select('id').eq('user_id', user_id).eq('name', 'Other').execute()
        if not other_category.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Other category not found. Cannot delete category."
            )
        
        other_category_id = other_category.data[0]['id']
        
        # Move all expenses from this category to "Other"
        expenses_update = supabase.table('expenses').update({
            'category_id': other_category_id,
            'updated_at': 'now()'
        }).eq('category_id', category_id).execute()
        
        # Delete the category
        result = supabase.table('categories').delete().eq('id', category_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete category"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Delete category error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete category: {str(e)}"
        )

@router.get("/{category_id}/expenses-count")
async def get_category_expenses_count(category_id: str, current_user = Depends(get_current_user)):
    """Get count of expenses in a category"""
    try:
        user_id = current_user['id']
        
        # Verify category belongs to user
        category_check = supabase.table('categories').select('id').eq('id', category_id).eq('user_id', user_id).execute()
        if not category_check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        # Count expenses
        result = supabase.table('expenses').select('id', count='exact').eq('category_id', category_id).execute()
        
        return {"count": result.count or 0}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Get expenses count error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get expenses count: {str(e)}"
        )