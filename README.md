# Competency Tracker

A full-stack application for tracking employee skills and competencies with advanced querying and analytics capabilities.

## 🏗️ Tech Stack

**Backend:**
- FastAPI (Python)
- PostgreSQL with SQLAlchemy ORM
- Pydantic for data validation
- Pandas for Excel import/export

**Frontend:**
- React 19 + Vite
- React Router for navigation
- Tailwind CSS for styling
- Lucide React for icons

---

## 📋 Prerequisites

- **Python 3.11+** ([Download](https://www.python.org/downloads/))
- **Node.js 18+** & npm ([Download](https://nodejs.org/))
- **PostgreSQL 14+** ([Download](https://www.postgresql.org/download/))

---

## 🚀 Quick Start

### 1️⃣ Backend Setup

```bash
# Navigate to backend folder
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Mac/Linux:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
# Copy the template and edit with your database credentials
copy .env.template .env
# Edit .env and update DATABASE_URL with your PostgreSQL connection string

# Run the server
uvicorn main:app --reload
```

Backend will be running at: **http://localhost:8000**
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

---

### 2️⃣ Frontend Setup

```bash
# Navigate to frontend folder (open new terminal)
cd frontend

# Install dependencies
npm install

# Configure environment
# Copy the template
copy .env.example .env
# .env is already configured for local development (http://localhost:8000)

# Run the development server
npm run dev
```

Frontend will be running at: **http://localhost:5173**

---

## 🗄️ Database Setup

### Option 1: Local PostgreSQL

1. Install PostgreSQL
2. Create database:
   ```sql
   CREATE DATABASE competency_tracker;
   ```
3. Update `backend/.env`:
   ```properties
   DATABASE_URL=postgresql+psycopg://postgres:yourpassword@localhost:5432/competency_tracker
   ```

### Option 2: Azure PostgreSQL

1. Update `backend/.env` with Azure connection string:
   ```properties
   DATABASE_URL=postgresql+psycopg://username:password@host.postgres.database.azure.com:5432/competency_tracker?sslmode=require
   ```

**Note:** Tables are auto-created on first run.

---

## 📁 Project Structure

```
competency_tracker/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # API endpoints
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   └── db/              # Database config
│   ├── main.py              # FastAPI app entry
│   ├── requirements.txt     # Python dependencies
│   └── .env.template        # Environment template
├── frontend/
│   ├── src/
│   │   ├── pages/           # Page components
│   │   ├── components/      # Reusable components
│   │   ├── services/        # API services
│   │   └── app/             # App setup & routing
│   ├── package.json         # Node dependencies
│   └── .env.example         # Frontend env template
└── README.md
```

---

## 🎯 Features

- **Dashboard** - Overview of organizational skill coverage and metrics
- **Capability Finder** - Advanced query builder to find employees by skills
- **Taxonomy** - Browse skill categories and hierarchies
- **Employee Profiles** - View and manage individual employee skills
- **Excel Import/Export** - Bulk data operations
- **Skill History Tracking** - Audit trail for skill changes

---

## 🔧 Development Commands

### Backend
```bash
# Run with auto-reload
uvicorn main:app --reload

# Run tests
pytest

# Create migration
alembic revision --autogenerate -m "description"
```

### Frontend
```bash
# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

---

## 📝 Environment Variables

### Backend (.env)
| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+psycopg://user:pass@host:5432/db` |
| `FASTAPI_ENV` | Environment mode | `development` or `production` |
| `LOG_LEVEL` | Logging level | `INFO`, `DEBUG`, `ERROR` |
| `SECRET_KEY` | Security key (production) | Random string |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:5173` |

### Frontend (.env)
| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API URL | `http://localhost:8000` |

---

## 🐛 Troubleshooting

### Backend won't start
- **Database connection timeout**: Check PostgreSQL is running and credentials are correct
- **Port 8000 already in use**: Kill process or change port in uvicorn command

### Frontend won't start
- **Port 5173 already in use**: Vite will auto-increment to 5174, 5175, etc.
- **API calls failing**: Verify `VITE_API_BASE_URL` in frontend/.env matches backend URL

### Database errors
- **"relation does not exist"**: Tables auto-create on first API call. Try the /health endpoint first.
- **"integer out of range"**: Excel import issue. Check for NaN values in numeric columns.

---

## 📄 License

ISC

---

## 👥 Contributing

1. Create feature branch
2. Make changes
3. Test locally (backend + frontend)
4. Submit pull request

---

## 📞 Support

For issues or questions, please create an issue in the repository.
