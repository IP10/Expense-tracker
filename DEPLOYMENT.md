# Render Deployment Guide

## Prerequisites
- GitHub account
- Render account (free)
- Your environment variable values

## Environment Variables Required
Set these in Render dashboard:
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase anon key  
- `SUPABASE_SERVICE_KEY` - Your Supabase service role key
- `JWT_SECRET` - Secret key for JWT tokens
- `ANTHROPIC_API_KEY` - Your Claude API key
- `JWT_ALGORITHM` - Set to `HS256` (optional, has default)

## Deployment Steps

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

2. **Deploy on Render**
   - Go to [render.com](https://render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the `backend/Expense-tracker` folder as root directory
   - Render will auto-detect the `render.yaml` configuration

3. **Set Environment Variables**
   - In Render dashboard, go to your service
   - Navigate to "Environment" tab
   - Add all required environment variables listed above

4. **Deploy**
   - Render will automatically deploy from your `render.yaml` config
   - Your API will be available at `https://your-service-name.onrender.com`

## Testing Deployment
Visit `https://your-service-name.onrender.com/health` to verify the API is running.