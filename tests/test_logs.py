import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from main import app
from app.database import get_db
from app.models.log import Log, SeverityLevel, Base

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def client():
    """Create a new database and client for each test"""
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)

class TestLogCRUD:
    """Test CRUD operations for logs"""

    def test_create_log(self, client):
        """Test creating a new log"""
        log_data = {
            "message": "Test log message",
            "severity": "INFO",
            "source": "test-service"
        }
        response = client.post("/logs", json=log_data)
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == log_data["message"]
        assert data["severity"] == log_data["severity"]
        assert data["source"] == log_data["source"]
        assert "id" in data
        assert "timestamp" in data

    def test_create_log_validation(self, client):
        """Test log creation validation"""
        # Test message too short
        response = client.post("/logs", json={
            "message": "ab",
            "severity": "INFO",
            "source": "test-service"
        })
        assert response.status_code == 400

        # Test message too long
        response = client.post("/logs", json={
            "message": "a" * 5001,
            "severity": "INFO",
            "source": "test-service"
        })
        assert response.status_code == 400

        # Test source too short
        response = client.post("/logs", json={
            "message": "Test message",
            "severity": "INFO",
            "source": "a"
        })
        assert response.status_code == 400

    def test_get_logs(self, client):
        """Test retrieving paginated logs"""
        # Create test logs
        for i in range(5):
            client.post("/logs", json={
                "message": f"Test message {i}",
                "severity": "INFO",
                "source": "test-service"
            })

        response = client.get("/logs")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 5
        assert data["page"] == 1
        assert data["total_pages"] == 1

    def test_get_logs_filtering(self, client):
        """Test log filtering"""
        # Create logs with different severities
        client.post("/logs", json={"message": "Info log", "severity": "INFO", "source": "service-a"})
        client.post("/logs", json={"message": "Error log", "severity": "ERROR", "source": "service-b"})
        client.post("/logs", json={"message": "Debug log", "severity": "DEBUG", "source": "service-a"})

        # Filter by severity
        response = client.get("/logs?severity=INFO")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["severity"] == "INFO"

        # Filter by source
        response = client.get("/logs?source=service-a")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    def test_get_log_by_id(self, client):
        """Test retrieving a specific log"""
        # Create a log
        create_response = client.post("/logs", json={
            "message": "Test log",
            "severity": "INFO",
            "source": "test-service"
        })
        log_id = create_response.json()["id"]

        # Get the log
        response = client.get(f"/logs/{log_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == log_id
        assert data["message"] == "Test log"

    def test_get_nonexistent_log(self, client):
        """Test retrieving a non-existent log"""
        response = client.get("/logs/99999")
        assert response.status_code == 404

    def test_update_log(self, client):
        """Test updating a log"""
        # Create a log
        create_response = client.post("/logs", json={
            "message": "Original message",
            "severity": "INFO",
            "source": "test-service"
        })
        log_id = create_response.json()["id"]

        # Update the log
        update_data = {"message": "Updated message", "severity": "WARNING"}
        response = client.put(f"/logs/{log_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Updated message"
        assert data["severity"] == "WARNING"

    def test_delete_log(self, client):
        """Test deleting a log"""
        # Create a log
        create_response = client.post("/logs", json={
            "message": "Test log",
            "severity": "INFO",
            "source": "test-service"
        })
        log_id = create_response.json()["id"]

        # Delete the log
        response = client.delete(f"/logs/{log_id}")
        assert response.status_code == 200

        # Verify deletion
        response = client.get(f"/logs/{log_id}")
        assert response.status_code == 404

class TestLogSearch:
    """Test log search and aggregation"""

    def test_search_by_severity(self, client):
        """Test searching logs by severity"""
        # Create test data
        client.post("/logs", json={"message": "Info 1", "severity": "INFO", "source": "service-a"})
        client.post("/logs", json={"message": "Info 2", "severity": "INFO", "source": "service-a"})
        client.post("/logs", json={"message": "Error 1", "severity": "ERROR", "source": "service-a"})

        response = client.get("/logs/search?group_by=severity")
        assert response.status_code == 200
        data = response.json()
        assert len(data["aggregations"]) >= 2
        assert data["total_count"] == 3

    def test_search_by_source(self, client):
        """Test searching logs by source"""
        client.post("/logs", json={"message": "Log 1", "severity": "INFO", "source": "service-a"})
        client.post("/logs", json={"message": "Log 2", "severity": "INFO", "source": "service-b"})
        client.post("/logs", json={"message": "Log 3", "severity": "INFO", "source": "service-a"})

        response = client.get("/logs/search?group_by=source")
        assert response.status_code == 200
        data = response.json()
        aggregations = data["aggregations"]

        service_a = next((a for a in aggregations if a["source"] == "service-a"), None)
        assert service_a is not None
        assert service_a["count"] == 2

class TestLogExport:
    """Test log export functionality"""

    def test_export_csv(self, client):
        """Test exporting logs as CSV"""
        # Create test logs
        client.post("/logs", json={"message": "Test log 1", "severity": "INFO", "source": "test-service"})
        client.post("/logs", json={"message": "Test log 2", "severity": "ERROR", "source": "test-service"})

        response = client.get("/logs/export/csv")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "Content-Disposition" in response.headers
        assert "logs_export_" in response.headers["Content-Disposition"]

        # Verify CSV content
        csv_content = response.text
        assert "ID,Timestamp,Severity,Source,Message" in csv_content
        assert "Test log 1" in csv_content
        assert "Test log 2" in csv_content

    def test_export_csv_with_filters(self, client):
        """Test exporting filtered logs as CSV"""
        client.post("/logs", json={"message": "Info log", "severity": "INFO", "source": "service-a"})
        client.post("/logs", json={"message": "Error log", "severity": "ERROR", "source": "service-b"})

        response = client.get("/logs/export/csv?severity=INFO")
        assert response.status_code == 200
        csv_content = response.text
        assert "Info log" in csv_content
        assert "Error log" not in csv_content

class TestHistogram:
    """Test histogram functionality"""

    def test_get_histogram(self, client):
        """Test getting severity histogram"""
        # Create test data
        client.post("/logs", json={"message": "Info 1", "severity": "INFO", "source": "service-a"})
        client.post("/logs", json={"message": "Info 2", "severity": "INFO", "source": "service-a"})
        client.post("/logs", json={"message": "Error 1", "severity": "ERROR", "source": "service-a"})

        response = client.get("/logs/histogram")
        assert response.status_code == 200
        data = response.json()
        assert "histogram" in data
        assert "filters" in data

        histogram = data["histogram"]
        assert len(histogram) == 5  # All severity levels should be present

        info_entry = next((h for h in histogram if h["severity"] == "INFO"), None)
        assert info_entry is not None
        assert info_entry["count"] == 2

    def test_get_histogram_with_filters(self, client):
        """Test histogram with source filter"""
        client.post("/logs", json={"message": "Log 1", "severity": "INFO", "source": "service-a"})
        client.post("/logs", json={"message": "Log 2", "severity": "INFO", "source": "service-b"})

        response = client.get("/logs/histogram?source=service-a")
        assert response.status_code == 200
        data = response.json()

        info_entry = next((h for h in data["histogram"] if h["severity"] == "INFO"), None)
        assert info_entry is not None
        assert info_entry["count"] == 1
