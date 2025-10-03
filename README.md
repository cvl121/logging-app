# Logs Dashboard

A full-stack web application for managing and analyzing logs with an analytical dashboard.

## Overview

This application provides a comprehensive logging system with:
- REST API for log management (CRUD operations)
- Advanced filtering, searching, sorting, and pagination
- Analytical dashboard with interactive charts
- Real-time log aggregation and metrics

## Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: SQLite (default) / PostgreSQL (optional)
- **ORM**: SQLAlchemy
- **Features**:
  - RESTful API endpoints
  - Input validation with Pydantic
  - CORS enabled for frontend integration
  - Automatic database initialization

### Frontend
- **Framework**: Next.js 14 with TypeScript
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **HTTP Client**: Axios
- **Features**:
  - Server-side rendering
  - Responsive design
  - Interactive data visualizations

## Project Structure

```
logging-app/
├── app/                      # Backend application
│   ├── models/              # Database models
│   │   └── log.py          # Log model with severity levels
│   ├── routers/            # API route handlers
│   │   └── logs.py         # Log endpoints
│   ├── schemas/            # Pydantic schemas
│   │   └── log.py          # Request/response models
│   └── database.py         # Database configuration
├── frontend/                # Next.js frontend
│   ├── components/         # Reusable React components
│   ├── pages/              # Next.js pages/routes
│   ├── lib/                # Utilities (API client)
│   ├── types/              # TypeScript type definitions
│   └── styles/             # Global styles
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Prerequisites

- **Python**: 3.8 or higher
- **Node.js**: 18.0 or higher
- **npm**: Latest version

**Note**: PostgreSQL is optional. The application uses SQLite by default for easy local development.

## Quick Start

### 1. Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start the backend server
python main.py
```

The backend API will be available at: **http://localhost:8000**

API Documentation (Swagger UI): **http://localhost:8000/docs**

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend will be available at: **http://localhost:3000**

### 3. Access the Application

Visit these URLs in your browser:
- **Dashboard**: http://localhost:3000 - View analytics and charts
- **Logs List**: http://localhost:3000/logs - Browse, search, filter, and sort logs
- **Create Log**: http://localhost:3000/logs/create - Create new log entries
- **API Docs**: http://localhost:8000/docs - Interactive API documentation

## Database Configuration

### SQLite (Default)
No setup required! The database file (`logs.db`) is automatically created in the project root on first run.

### PostgreSQL (Optional)
To use PostgreSQL instead of SQLite:

1. Install and start PostgreSQL
2. Create a database:
   ```bash
   createdb logsdb
   ```
3. Create a `.env` file in the project root:
   ```bash
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/logsdb
   ```
4. Restart the backend server

## Stopping the Application

To stop the running services:

```bash
# Stop backend
pkill -f "python main.py"

# Stop frontend
pkill -f "next dev"
```

## API Endpoints

### Logs Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/logs` | Get paginated logs with filters |
| GET | `/logs/{id}` | Get specific log by ID |
| POST | `/logs` | Create a new log |
| PUT | `/logs/{id}` | Update a log |
| DELETE | `/logs/{id}` | Delete a log |
| GET | `/logs/search` | Get aggregated log data |
| GET | `/logs/export/csv` | Export logs as CSV |
| GET | `/logs/histogram` | Get severity distribution histogram |

### Query Parameters for `/logs`

- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 50, max: 1000)
- `severity`: Filter by severity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `source`: Filter by source
- `start_date`: Filter logs from this date (ISO 8601 format)
- `end_date`: Filter logs until this date (ISO 8601 format)
- `search`: Search in message field
- `sort_by`: Field to sort by (timestamp, severity, source)
- `sort_order`: Sort order (asc, desc)

### Query Parameters for `/logs/search`

- `severity`: Filter by severity
- `source`: Filter by source
- `start_date`: Filter from date
- `end_date`: Filter until date
- `group_by`: Group by field (severity, source, date, hour)

## Frontend Pages

### Dashboard (`/`)
- Overview of log metrics
- Severity distribution pie chart
- Top sources bar chart
- Log trend over time line chart
- **Severity distribution histogram** with source filtering
- Severity breakdown table
- Date range filter

### Logs List (`/logs`)
- Paginated table of all logs
- Search, filter, and sort functionality
- **CSV export button** (exports current filtered results)
- Click to view details
- Quick delete action

### Log Detail (`/logs/{id}`)
- View complete log details
- Edit log information with validation
- Delete log

### Create Log (`/logs/create`)
- Form to create new log entries
- Client-side validation with error messages
- Character counter for message field

## Database Schema

### Logs Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| timestamp | DateTime | When the log was created |
| message | String | Log message content |
| severity | Enum | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| source | String | Source of the log (e.g., service name) |

Indexes are created on: `timestamp`, `severity`, and `source` for optimized queries.

## Usage Examples

### Creating a Log (curl)

```bash
curl -X POST "http://localhost:8000/logs" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "User authentication successful",
    "severity": "INFO",
    "source": "auth-service"
  }'
```

### Filtering Logs

```bash
# Get ERROR logs from the last 24 hours
curl "http://localhost:8000/logs?severity=ERROR&start_date=2024-01-01T00:00:00"

# Search for specific message
curl "http://localhost:8000/logs?search=authentication"
```

### Getting Log Data

```bash
# Get logs grouped by severity
curl "http://localhost:8000/logs/search?group_by=severity"

# Get daily log counts
curl "http://localhost:8000/logs/search?group_by=date&start_date=2024-01-01T00:00:00"
```

## Features

### CSV Export
Export filtered logs to CSV format:
- Includes all current filters (severity, source, date range, search)
- Downloads timestamped CSV file
- Contains: ID, Timestamp, Severity, Source, Message

### Histogram Visualization
Interactive severity distribution histogram:
- Color-coded by severity level
- Filterable by source
- Updates based on selected date range
- Shows all severity levels (even with 0 count)

### Input Validation
- **Message**: 3-5000 characters
- **Source**: 2-255 characters, alphanumeric + hyphens/underscores/dots
- **Timestamp**: Cannot be in the future
- Real-time validation with inline error messages

### Error Handling
- Comprehensive error messages from API
- Frontend axios interceptors for request/response logging
- Backend try-catch blocks with proper HTTP status codes
- Transaction rollback on database errors

### Logging & Debugging
- Frontend: Console logs with component prefixes (`[Dashboard]`, `[LogsPage]`, etc.)
- Backend: Python logging with INFO/WARNING/ERROR levels
- Request/response logging for all API calls

## Development

### Running Tests

Backend tests:
```bash
# Install test dependencies
pip install pytest httpx

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_logs.py -v

# Run with coverage
pytest tests/ --cov=app
```

**Test Results**: 13/24 tests passing (54% pass rate)
- ✅ CRUD operations
- ✅ Filtering and search
- ✅ CSV export
- ✅ API health checks
- ⚠️ Some integration tests need database configuration fixes

Frontend tests (not implemented):
```bash
cd frontend
npm test
```

### Building for Production

Backend:
```bash
# The application can be served with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000
```

Frontend:
```bash
cd frontend
npm run build
npm start
```

## Docker Deployment (Optional)

A `docker-compose.yml` file can be created to run the entire stack:

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: logsdb
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://postgres:postgres@db:5432/logsdb
    depends_on:
      - db

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    depends_on:
      - backend

volumes:
  postgres_data:
```

## Troubleshooting

### Backend Issues

**Database connection errors:**
- Verify PostgreSQL is running: `pg_isready`
- Check database exists: `psql -l`
- Verify DATABASE_URL in .env file

**Port already in use:**
- Change the port in `main.py`: `uvicorn.run("main:app", port=8001)`

### Frontend Issues

**API connection errors:**
- Ensure backend is running on port 8000
- Check NEXT_PUBLIC_API_URL in `.env.local`
- Verify CORS is enabled in backend

**Module not found:**
- Delete `node_modules` and `.next` folders
- Run `npm install` again
