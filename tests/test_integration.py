import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from main import app
from app.database import get_db
from app.models.log import Base

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_integration.db"
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

class TestEndToEndWorkflow:
    """Test complete end-to-end workflows"""

    def test_complete_log_lifecycle(self, client):
        """Test creating, reading, updating, and deleting a log"""
        # Create
        create_response = client.post("/logs", json={
            "message": "Initial message",
            "severity": "INFO",
            "source": "integration-test"
        })
        assert create_response.status_code == 201
        log_id = create_response.json()["id"]

        # Read
        read_response = client.get(f"/logs/{log_id}")
        assert read_response.status_code == 200
        assert read_response.json()["message"] == "Initial message"

        # Update
        update_response = client.put(f"/logs/{log_id}", json={
            "message": "Updated message",
            "severity": "WARNING"
        })
        assert update_response.status_code == 200
        assert update_response.json()["message"] == "Updated message"
        assert update_response.json()["severity"] == "WARNING"

        # Verify update
        verify_response = client.get(f"/logs/{log_id}")
        assert verify_response.json()["message"] == "Updated message"

        # Delete
        delete_response = client.delete(f"/logs/{log_id}")
        assert delete_response.status_code == 200

        # Verify deletion
        final_response = client.get(f"/logs/{log_id}")
        assert final_response.status_code == 404

    def test_dashboard_workflow(self, client):
        """Test dashboard data aggregation workflow"""
        # Create diverse log data
        test_data = [
            {"message": "User login", "severity": "INFO", "source": "auth-service"},
            {"message": "User logout", "severity": "INFO", "source": "auth-service"},
            {"message": "Database error", "severity": "ERROR", "source": "database"},
            {"message": "API timeout", "severity": "WARNING", "source": "api-gateway"},
            {"message": "Critical failure", "severity": "CRITICAL", "source": "payment-service"},
        ]

        for log in test_data:
            response = client.post("/logs", json=log)
            assert response.status_code == 201

        # Test severity aggregation
        severity_response = client.get("/logs/search?group_by=severity")
        assert severity_response.status_code == 200
        severity_data = severity_response.json()
        assert severity_data["total_count"] == 5

        # Test source aggregation
        source_response = client.get("/logs/search?group_by=source")
        assert source_response.status_code == 200
        source_data = source_response.json()
        assert len(source_data["aggregations"]) == 4  # 4 unique sources

        # Test histogram
        histogram_response = client.get("/logs/histogram")
        assert histogram_response.status_code == 200
        histogram_data = histogram_response.json()
        assert "histogram" in histogram_data

    def test_filtering_and_export_workflow(self, client):
        """Test filtering logs and exporting results"""
        # Create logs with different attributes
        logs = [
            {"message": "Service A info", "severity": "INFO", "source": "service-a"},
            {"message": "Service A error", "severity": "ERROR", "source": "service-a"},
            {"message": "Service B info", "severity": "INFO", "source": "service-b"},
        ]

        for log in logs:
            client.post("/logs", json=log)

        # Filter by source
        filter_response = client.get("/logs?source=service-a")
        assert filter_response.status_code == 200
        filtered_data = filter_response.json()
        assert filtered_data["total"] == 2

        # Export filtered data
        export_response = client.get("/logs/export/csv?source=service-a")
        assert export_response.status_code == 200
        csv_content = export_response.text
        assert "Service A info" in csv_content
        assert "Service A error" in csv_content
        assert "Service B info" not in csv_content

    def test_pagination_workflow(self, client):
        """Test pagination across multiple pages"""
        # Create 25 logs
        for i in range(25):
            client.post("/logs", json={
                "message": f"Log number {i}",
                "severity": "INFO",
                "source": "test-service"
            })

        # Get first page (default 50 per page, so should get all)
        page1_response = client.get("/logs?page=1&page_size=10")
        assert page1_response.status_code == 200
        page1_data = page1_response.json()
        assert len(page1_data["items"]) == 10
        assert page1_data["total"] == 25
        assert page1_data["total_pages"] == 3

        # Get second page
        page2_response = client.get("/logs?page=2&page_size=10")
        assert page2_response.status_code == 200
        page2_data = page2_response.json()
        assert len(page2_data["items"]) == 10

        # Get third page
        page3_response = client.get("/logs?page=3&page_size=10")
        assert page3_response.status_code == 200
        page3_data = page3_response.json()
        assert len(page3_data["items"]) == 5

    def test_search_functionality(self, client):
        """Test search functionality"""
        # Create logs with searchable content
        logs = [
            {"message": "User authentication failed", "severity": "ERROR", "source": "auth"},
            {"message": "Database connection timeout", "severity": "ERROR", "source": "db"},
            {"message": "User successfully authenticated", "severity": "INFO", "source": "auth"},
        ]

        for log in logs:
            client.post("/logs", json=log)

        # Search for "authentication"
        search_response = client.get("/logs?search=authentication")
        assert search_response.status_code == 200
        search_data = search_response.json()
        assert search_data["total"] == 2

        # Search for "timeout"
        timeout_response = client.get("/logs?search=timeout")
        assert timeout_response.status_code == 200
        timeout_data = timeout_response.json()
        assert timeout_data["total"] == 1

    def test_sorting_workflow(self, client):
        """Test sorting functionality"""
        # Create logs
        client.post("/logs", json={"message": "B message", "severity": "WARNING", "source": "service-b"})
        client.post("/logs", json={"message": "A message", "severity": "INFO", "source": "service-a"})
        client.post("/logs", json={"message": "C message", "severity": "ERROR", "source": "service-c"})

        # Sort by source ascending
        asc_response = client.get("/logs?sort_by=source&sort_order=asc")
        assert asc_response.status_code == 200
        asc_data = asc_response.json()
        assert asc_data["items"][0]["source"] == "service-a"

        # Sort by severity descending (default)
        desc_response = client.get("/logs?sort_by=severity&sort_order=desc")
        assert desc_response.status_code == 200

    def test_error_handling_workflow(self, client):
        """Test error handling across the application"""
        # Try to get non-existent log
        response = client.get("/logs/99999")
        assert response.status_code == 404

        # Try to update non-existent log
        response = client.put("/logs/99999", json={"message": "Update"})
        assert response.status_code == 404

        # Try to delete non-existent log
        response = client.delete("/logs/99999")
        assert response.status_code == 404

        # Try to create log with invalid data
        response = client.post("/logs", json={
            "message": "a",  # Too short
            "severity": "INFO",
            "source": "test"
        })
        assert response.status_code == 400

    def test_date_filtering_workflow(self, client):
        """Test date range filtering"""
        now = datetime.utcnow()

        # Create log from yesterday
        past_log = {
            "message": "Old log",
            "severity": "INFO",
            "source": "test",
            "timestamp": (now - timedelta(days=1)).isoformat()
        }
        client.post("/logs", json=past_log)

        # Create log from today
        current_log = {
            "message": "Current log",
            "severity": "INFO",
            "source": "test"
        }
        client.post("/logs", json=current_log)

        # Filter to only get today's logs
        start_date = now.strftime("%Y-%m-%dT00:00:00")
        response = client.get(f"/logs?start_date={start_date}")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

class TestAPIHealthAndMetadata:
    """Test API health and metadata endpoints"""

    def test_root_endpoint(self, client):
        """Test root endpoint returns API info"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data or "version" in data

    def test_docs_available(self, client):
        """Test that API docs are accessible"""
        response = client.get("/docs")
        assert response.status_code == 200
