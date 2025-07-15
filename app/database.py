from supabase import create_client, Client
from app.config import settings

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

async def init_db():
    """Initialize database tables if they don't exist"""
    try:
        # Check if tables exist by trying to select from them
        supabase.table('users').select('id').limit(1).execute()
        supabase.table('categories').select('id').limit(1).execute()
        supabase.table('expenses').select('id').limit(1).execute()
        print("✅ Database tables verified")
    except Exception as e:
        print(f"⚠️  Database initialization error: {e}")
        print("Please ensure Supabase tables are created with the following schema:")
        print_schema()

def print_schema():
    """Print the required database schema"""
    schema = """
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

    -- Indexes for better performance
    CREATE INDEX idx_expenses_user_id ON expenses(user_id);
    CREATE INDEX idx_expenses_date ON expenses(date);
    CREATE INDEX idx_expenses_category_id ON expenses(category_id);
    CREATE INDEX idx_categories_user_id ON categories(user_id);

    -- Insert default categories
    INSERT INTO categories (name, emoji, is_system) VALUES
    ('Food', '🍽️', true),
    ('Transport', '🚗', true),
    ('Entertainment', '🎬', true),
    ('Shopping', '🛒', true),
    ('Healthcare', '🏥', true),
    ('Utilities', '💡', true),
    ('Education', '📚', true),
    ('Other', '📝', true);
    """
    print(schema)