# Secure Image Upload Platform

A full-stack web application that allows authenticated users to securely upload image files to Azure Blob Storage with metadata tracking in PostgreSQL.

## Features

- **Authentication**: Secure login with Auth0
- **File Upload**: Image upload with validation (JPG, PNG, GIF, max 5MB)
- **Cloud Storage**: Files stored in Azure Blob Storage with unique filenames
- **Database Tracking**: Upload metadata stored in PostgreSQL
- **User Management**: Users can view their uploaded files
- **Security**: JWT token validation, file type validation, and size limits

## Tech Stack

### Frontend
- React 19
- Auth0 React SDK
- Axios for API calls
- Vite for build tooling

### Backend
- FastAPI (Python)
- SQLAlchemy for database ORM
- Python-Jose for JWT verification
- Azure Storage SDK
- Pillow for image validation

### Infrastructure
- PostgreSQL database
- Azure Blob Storage
- Auth0 for authentication

## Prerequisites

- Node.js 18+ and npm
- Python 3.8+
- PostgreSQL (or Docker)
- Azure Storage Account
- Auth0 Account

## Setup Instructions

### 1. Clone and Install Dependencies

```bash
# Install frontend dependencies
npm install

# Install backend dependencies
cd backend
pip install -r requirements.txt
```

### 2. Database Setup

#### Option A: Using Docker (Recommended)
```bash
docker-compose up -d
```

#### Option B: Local PostgreSQL
```bash
# Make the setup script executable
chmod +x database_setup.sh

# Run the setup script
./database_setup.sh
```

### 3. Azure Blob Storage Setup

1. Create an Azure Storage Account
2. Create a container named "images" (or customize in .env)
3. Get the connection string from Azure Portal

### 4. Auth0 Setup

1. Create an Auth0 account and application
2. Configure the following settings:
   - **Application Type**: Single Page Application
   - **Allowed Callback URLs**: `http://localhost:5173`
   - **Allowed Logout URLs**: `http://localhost:5173`
   - **Allowed Web Origins**: `http://localhost:5173`
3. Create an API in Auth0:
   - **Identifier**: Use this as your audience
   - **Signing Algorithm**: RS256

### 5. Environment Configuration

#### Frontend (.env)
```env
VITE_AUTH0_DOMAIN=your-auth0-domain.auth0.com
VITE_AUTH0_CLIENT_ID=your-auth0-client-id
VITE_AUTH0_AUDIENCE=your-api-identifier
VITE_API_BASE_URL=http://localhost:8000
```

#### Backend (.env)
```env
# Auth0 Configuration
AUTH0_DOMAIN=your-auth0-domain.auth0.com
AUTH0_AUDIENCE=your-api-identifier

# Database Configuration
DATABASE_URL=postgresql://image_upload_user:your_secure_password_here@localhost:5432/image_upload_db

# Azure Storage Configuration
AZURE_STORAGE_CONNECTION_STRING=your-azure-storage-connection-string
AZURE_STORAGE_CONTAINER_NAME=images

# App Configuration
MAX_FILE_SIZE=5242880
ALLOWED_EXTENSIONS=jpg,jpeg,png,gif
```

### 6. Run the Application

#### Start the backend:
```bash
cd backend
python main.py
```
The API will be available at http://localhost:8000

#### Start the frontend:
```bash
npm run dev
```
The frontend will be available at http://localhost:5173

## API Endpoints

### Authentication Required
All endpoints except `/` and `/health` require a valid JWT token.

- `GET /` - API status
- `GET /health` - Health check
- `POST /upload` - Upload an image file
- `GET /files` - Get user's uploaded files

## Security Features

1. **JWT Validation**: All protected endpoints validate Auth0 JWT tokens
2. **File Type Validation**: Only image files (JPG, PNG, GIF) are allowed
3. **File Size Limits**: Maximum 5MB file size
4. **Image Content Validation**: Uses Pillow to verify actual image content
5. **Unique Filenames**: Prevents filename conflicts and direct file access
6. **User Isolation**: Users can only access their own files

## Project Structure

```
├── src/                    # Frontend React application
│   ├── components/         # React components
│   ├── utils/             # Utility functions
│   └── ...
├── backend/               # FastAPI backend
│   ├── main.py           # Main application file
│   └── requirements.txt  # Python dependencies
├── public/               # Static assets
├── docker-compose.yml    # PostgreSQL setup
├── init.sql             # Database schema
└── README.md            # This file
```

## Deployment Considerations

### Security Checklist
- [ ] Use environment variables for all secrets
- [ ] Enable HTTPS in production
- [ ] Configure CORS properly for production domains
- [ ] Use strong database passwords
- [ ] Regularly rotate Azure storage keys
- [ ] Enable Azure Blob Storage access logging
- [ ] Set up proper Auth0 production settings

### Production Setup
1. **Frontend**: Deploy to Vercel, Netlify, or similar
2. **Backend**: Deploy to Heroku, Azure App Service, or similar
3. **Database**: Use managed PostgreSQL (Azure Database, AWS RDS, etc.)
4. **Storage**: Azure Blob Storage (already configured)

### Environment Variables for Production
Update the URLs and domains in your `.env` files to match your production environment.

## Troubleshooting

### Common Issues

1. **CORS Errors**: Ensure your frontend URL is in the backend CORS settings
2. **Auth0 Errors**: Check domain, client ID, and callback URLs
3. **Database Connection**: Verify PostgreSQL is running and credentials are correct
4. **Azure Storage**: Confirm connection string and container exists
5. **File Upload Errors**: Check file size and type restrictions

### Development Tools

- Backend API docs: http://localhost:8000/docs
- Database connection test: Check logs when starting the backend
- Auth0 logs: Available in Auth0 dashboard
