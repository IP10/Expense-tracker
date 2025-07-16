from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn

from app.auth import verify_token
from app.routers import auth, expenses, reports, categories
from app.database import init_db

app = FastAPI(
    title="Expense Tracker API",
    description="A comprehensive expense tracking API with AI-powered categorization",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    try:
        await init_db()
    except Exception as e:
        print(f"❌ Startup error: {str(e)}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(expenses.router, prefix="/api/expenses", tags=["Expenses"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(categories.router, prefix="/api/categories", tags=["Categories"])

@app.get("/")
async def root():
    try:
        return {"message": "Expense Tracker API is running!", "version": "1.0.0"}
    except Exception as e:
        print(f"❌ Root endpoint error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Root endpoint failed: {str(e)}"
        )

@app.get("/health")
async def health_check():
    try:
        return {"status": "healthy", "message": "API is operational"}
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)