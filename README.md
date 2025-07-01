# Expense Tracker App

A comprehensive expense tracking application with Android frontend and Python FastAPI backend, featuring AI-powered expense categorization.

## Features

### Core Functionality
- ✅ User registration and authentication
- ✅ Add expenses with automatic AI categorization
- ✅ View and manage expense list
- ✅ Generate reports (this month, last month, custom date range)
- ✅ Category management with manual editing
- ✅ INR currency support

### Technical Features
- 🤖 Claude Sonnet AI-powered expense categorization with keyword fallback
- 📱 Material Design 3 Android app
- 🔒 JWT-based authentication
- 📊 Real-time expense analytics
- ☁️ Supabase backend integration

## Architecture

```
┌─────────────────┐    HTTP/REST     ┌─────────────────┐    SQL    ┌─────────────────┐
│   Android App   │ ──────────────── │  FastAPI Backend │ ───────── │    Supabase     │
│  (Jetpack       │                  │  (Python)       │           │   (PostgreSQL)  │
│   Compose)      │                  │                 │           │                 │
└─────────────────┘                  └─────────────────┘           └─────────────────┘
```

## Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL)
- **Authentication**: JWT tokens
- **AI**: Claude Sonnet API with keyword fallback
- **Testing**: Pytest

### Android App
- **UI**: Jetpack Compose + Material Design 3
- **Architecture**: MVVM with Hilt DI
- **Navigation**: Navigation Compose
- **Networking**: Retrofit + OkHttp
- **Testing**: JUnit + Espresso

## Setup Instructions

### Prerequisites
- Python 3.8+
- Android Studio (latest version)
- Supabase account

### Backend Setup

1. **Create Supabase Project**
   ```bash
   # Go to https://supabase.com and create a new project
   # Get your URL and API keys
   ```

2. **Database Schema**
   ```sql
   -- Run this in Supabase SQL editor
   -- Users table
   CREATE TABLE users (
       id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
       email varchar UNIQUE NOT NULL,
       full_name varchar NOT NULL,
       password_hash varchar NOT NULL,
       created_at timestamptz DEFAULT now(),
       updated_at timestamptz DEFAULT now()
   );

   -- Categories table
   CREATE TABLE categories (
       id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
       name varchar NOT NULL,
       emoji varchar,
       is_system boolean DEFAULT false,
       user_id uuid REFERENCES users(id) ON DELETE CASCADE,
       created_at timestamptz DEFAULT now(),
       updated_at timestamptz DEFAULT now(),
       UNIQUE(name, user_id)
   );

   -- Expenses table
   CREATE TABLE expenses (
       id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
       user_id uuid REFERENCES users(id) ON DELETE CASCADE NOT NULL,
       amount decimal(10,2) NOT NULL CHECK (amount > 0),
       note varchar(500) NOT NULL,
       date date NOT NULL,
       category_id uuid REFERENCES categories(id) NOT NULL,
       created_at timestamptz DEFAULT now(),
       updated_at timestamptz DEFAULT now()
   );

   -- Indexes
   CREATE INDEX idx_expenses_user_id ON expenses(user_id);
   CREATE INDEX idx_expenses_date ON expenses(date);
   CREATE INDEX idx_expenses_category_id ON expenses(category_id);
   CREATE INDEX idx_categories_user_id ON categories(user_id);
   ```

3. **Backend Installation**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Environment Setup**
   ```bash
   cp .env.example .env
   # Edit .env with your Supabase and Claude API credentials:
   # SUPABASE_URL=your_supabase_url
   # SUPABASE_KEY=your_supabase_anon_key  
   # SUPABASE_SERVICE_KEY=your_supabase_service_key
   # JWT_SECRET=your_jwt_secret_key
   # ANTHROPIC_API_KEY=your_claude_api_key
   ```

5. **Run Backend**
   ```bash
   python main.py
   # API will be available at http://localhost:8000
   ```

### Android App Setup

1. **Open in Android Studio**
   ```bash
   # Open android-app folder in Android Studio
   ```

2. **Build Project**
   ```bash
   # Android Studio will automatically download dependencies
   # Make sure backend is running on localhost:8000
   ```

3. **Run App**
   ```bash
   # Use Android Studio's run button or
   ./gradlew installDebug
   ```

## Testing

### Backend Tests
```bash
cd backend
pytest -v
pytest tests/test_auth.py -v
pytest tests/test_expenses.py -v
pytest tests/test_ai_categorizer.py -v
```

### Android Tests
```bash
cd android-app
./gradlew test           # Unit tests
./gradlew connectedAndroidTest  # Integration tests
```

## API Documentation

### Authentication Endpoints
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user info

### Expense Endpoints
- `POST /api/expenses/` - Create expense
- `GET /api/expenses/` - List expenses (with filters)
- `GET /api/expenses/{id}` - Get expense details
- `PUT /api/expenses/{id}` - Update expense
- `DELETE /api/expenses/{id}` - Delete expense
- `POST /api/expenses/categorize-preview` - Preview categorization

### Category Endpoints
- `GET /api/categories/` - List categories
- `POST /api/categories/` - Create category
- `PUT /api/categories/{id}` - Update category
- `DELETE /api/categories/{id}` - Delete category

### Report Endpoints
- `POST /api/reports/` - Generate custom report
- `GET /api/reports/this-month` - This month report
- `GET /api/reports/last-month` - Last month report
- `GET /api/reports/last-n-months/{n}` - Last N months report
- `GET /api/reports/monthly-trend` - Monthly trend data
- `GET /api/reports/summary` - Overall summary

## AI Categorization

The app uses **Claude Sonnet AI** for intelligent expense categorization with keyword-based fallback. This provides:

### Default Categories
- 🍽️ **Food**: restaurant, lunch, coffee, grocery, etc.
- 🚗 **Transport**: uber, taxi, fuel, bus, flight, etc.
- 🎬 **Entertainment**: movie, netflix, gym, concert, etc.
- 🛒 **Shopping**: clothes, amazon, electronics, etc.
- 🏥 **Healthcare**: doctor, medicine, hospital, etc.
- 💡 **Utilities**: electricity, internet, rent, etc.
- 📚 **Education**: course, books, fees, etc.
- 📝 **Other**: fallback category

### Categorization Logic
1. **Claude AI Analysis**: Uses Claude Sonnet to understand context and nuances
2. **Indian Context Aware**: Recognizes Swiggy=Food, Ola=Transport, etc.
3. **Keyword Fallback**: Falls back to keyword matching if API unavailable
4. **Robust Error Handling**: Always provides a category, never fails

### Benefits of Claude Sonnet
- **Superior Context Understanding**: Better than keyword matching alone
- **Indian Market Awareness**: Understands local brands and services  
- **Cost Efficient**: Generally more cost-effective than GPT-4
- **Reliable Fallback**: Keyword system ensures 100% uptime

## Corner Cases Handled

### Data Validation
- ✅ Amount validation (positive, reasonable limits)
- ✅ Note length limits and required fields
- ✅ Date validation (no future dates beyond reasonable)
- ✅ Category ownership verification

### Error Handling
- ✅ Network timeouts and retries
- ✅ Authentication token expiry
- ✅ Database constraint violations
- ✅ Invalid input sanitization

### Edge Scenarios
- ✅ Empty expense lists
- ✅ Category deletion (moves to "Other")
- ✅ Concurrent data modifications
- ✅ Large dataset performance

## Development

### Code Structure

**Backend**
```
backend/
├── app/
│   ├── routers/         # API endpoints
│   ├── models.py        # Pydantic models
│   ├── auth.py          # Authentication logic
│   ├── database.py      # Database connection
│   ├── ai_categorizer.py # AI categorization
│   └── config.py        # Configuration
├── tests/               # Test files
└── main.py             # FastAPI app
```

**Android**
```
android-app/src/main/java/com/expensetracker/app/
├── data/                # Data layer (repositories, API)
├── domain/              # Business logic (models, use cases)
├── presentation/        # UI layer (Compose screens)
├── di/                  # Dependency injection
└── utils/               # Utility functions
```

### Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Testing Guidelines

- Write tests for all new features
- Maintain >80% code coverage
- Test both happy path and error scenarios
- Include integration tests for API endpoints

## Deployment

### Backend Deployment
- Deploy to platforms like Railway, Render, or AWS
- Set environment variables for production
- Use production Supabase instance

### Android Deployment
- Build release APK: `./gradlew assembleRelease`
- Upload to Google Play Store
- Update API endpoint to production URL

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support or questions:
- Create an issue in the repository
- Check existing documentation
- Review test files for usage examples