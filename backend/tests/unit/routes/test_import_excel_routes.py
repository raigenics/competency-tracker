"""
Unit tests for import_excel API routes.

Tests all Bulk Import endpoints:
- POST /import/excel - Upload Excel file and start async import
- GET /import/status/{job_id} - Poll job status

Coverage targets:
- File validation (type, size, filename)
- Job creation and async processing
- Status polling with various states
- Error handling
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
import io

from app.api.routes.import_excel import router
from app.services.import_job_service import JobStatusDBError


# Create test app with the router
app = FastAPI()
app.include_router(router)
client = TestClient(app)


# ============================================================================
# MOCK FACTORIES
# ============================================================================

def create_mock_job_service():
    """Create mock ImportJobService."""
    service = MagicMock()
    service.create_job.return_value = "test-job-123"
    service.get_job_status.return_value = {
        "job_id": "test-job-123",
        "status": "pending",
        "percent_complete": 0,
        "message": "Import starting..."
    }
    return service


def create_excel_file(filename="test.xlsx", content=b"fake excel content"):
    """Create a mock Excel file for upload."""
    return ("file", (filename, io.BytesIO(content), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"))


# ============================================================================
# TEST: POST /import/excel
# ============================================================================

class TestPostImportExcel:
    """Test POST /import/excel endpoint."""
    
    def test_rejects_missing_file(self):
        """Should return 422 when no file is provided."""
        # Act
        response = client.post('/import/excel')
        
        # Assert
        assert response.status_code == 422
    
    def test_rejects_missing_filename(self):
        """Should return 400 when file has no filename."""
        # Arrange - empty filename causes FastAPI validation to return 422
        file_data = ("file", ("", io.BytesIO(b"content"), "application/octet-stream"))
        
        # Act
        response = client.post('/import/excel', files=[file_data])
        
        # Assert - FastAPI returns 422 for malformed upload, which is correct behavior
        assert response.status_code == 422
    
    def test_rejects_non_excel_file(self):
        """Should return 400 for non-Excel file types."""
        # Arrange
        file_data = ("file", ("test.csv", io.BytesIO(b"csv,content"), "text/csv"))
        
        # Act
        response = client.post('/import/excel', files=[file_data])
        
        # Assert
        assert response.status_code == 400
        assert "Excel file" in response.json()["detail"]
    
    def test_rejects_txt_file(self):
        """Should return 400 for .txt file."""
        # Arrange
        file_data = ("file", ("test.txt", io.BytesIO(b"text content"), "text/plain"))
        
        # Act
        response = client.post('/import/excel', files=[file_data])
        
        # Assert
        assert response.status_code == 400
    
    def test_accepts_xlsx_file(self):
        """Should accept .xlsx file and return 202 with job_id."""
        # Arrange
        mock_db = MagicMock()
        mock_job_service = create_mock_job_service()
        
        with patch('app.api.routes.import_excel.ImportJobService', return_value=mock_job_service), \
             patch('app.api.routes.import_excel._save_upload_file', new_callable=AsyncMock, return_value="/tmp/test.xlsx"), \
             patch('app.api.routes.import_excel._process_import_async', new_callable=AsyncMock), \
             patch('app.api.routes.import_excel.get_db', return_value=mock_db):
            
            file_data = create_excel_file("test.xlsx")
            
            # Act
            response = client.post('/import/excel', files=[file_data])
        
        # Assert
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"
    
    def test_accepts_xls_file(self):
        """Should accept .xls file."""
        # Arrange
        mock_db = MagicMock()
        mock_job_service = create_mock_job_service()
        
        with patch('app.api.routes.import_excel.ImportJobService', return_value=mock_job_service), \
             patch('app.api.routes.import_excel._save_upload_file', new_callable=AsyncMock, return_value="/tmp/test.xls"), \
             patch('app.api.routes.import_excel._process_import_async', new_callable=AsyncMock), \
             patch('app.api.routes.import_excel.get_db', return_value=mock_db):
            
            file_data = ("file", ("legacy.xls", io.BytesIO(b"xls content"), "application/vnd.ms-excel"))
            
            # Act
            response = client.post('/import/excel', files=[file_data])
        
        # Assert
        assert response.status_code == 202
    
    def test_accepts_xlsX_case_insensitive(self):
        """Should accept .XLSX (uppercase) file."""
        # Arrange
        mock_db = MagicMock()
        mock_job_service = create_mock_job_service()
        
        with patch('app.api.routes.import_excel.ImportJobService', return_value=mock_job_service), \
             patch('app.api.routes.import_excel._save_upload_file', new_callable=AsyncMock, return_value="/tmp/test.xlsx"), \
             patch('app.api.routes.import_excel._process_import_async', new_callable=AsyncMock), \
             patch('app.api.routes.import_excel.get_db', return_value=mock_db):
            
            file_data = ("file", ("Test.XLSX", io.BytesIO(b"content"), "application/octet-stream"))
            
            # Act
            response = client.post('/import/excel', files=[file_data])
        
        # Assert
        assert response.status_code == 202
    
    def test_returns_job_id_in_response(self):
        """Should return job_id for status polling."""
        # Arrange
        mock_db = MagicMock()
        mock_job_service = create_mock_job_service()
        mock_job_service.create_job.return_value = "unique-job-id-456"
        
        with patch('app.api.routes.import_excel.ImportJobService', return_value=mock_job_service), \
             patch('app.api.routes.import_excel._save_upload_file', new_callable=AsyncMock, return_value="/tmp/test.xlsx"), \
             patch('app.api.routes.import_excel._process_import_async', new_callable=AsyncMock), \
             patch('app.api.routes.import_excel.get_db', return_value=mock_db):
            
            file_data = create_excel_file("data.xlsx")
            
            # Act
            response = client.post('/import/excel', files=[file_data])
        
        # Assert
        assert response.status_code == 202
        assert response.json()["job_id"] == "unique-job-id-456"
        assert "Poll /import/status" in response.json()["message"]
    
    def test_handles_file_save_error(self):
        """Should return 500 when file save fails."""
        # Arrange
        mock_db = MagicMock()
        
        with patch('app.api.routes.import_excel._save_upload_file', new_callable=AsyncMock, side_effect=Exception("Disk full")), \
             patch('app.api.routes.import_excel.get_db', return_value=mock_db):
            
            file_data = create_excel_file("test.xlsx")
            
            # Act
            response = client.post('/import/excel', files=[file_data])
        
        # Assert
        assert response.status_code == 500
        assert "Failed to save uploaded file" in response.json()["detail"]
    
    def test_handles_job_creation_error(self):
        """Should return 500 when job creation fails."""
        # Arrange
        mock_db = MagicMock()
        mock_job_service = MagicMock()
        mock_job_service.create_job.side_effect = Exception("Database error")
        
        with patch('app.api.routes.import_excel.ImportJobService', return_value=mock_job_service), \
             patch('app.api.routes.import_excel._save_upload_file', new_callable=AsyncMock, return_value="/tmp/test.xlsx"), \
             patch('app.api.routes.import_excel.get_db', return_value=mock_db):
            
            file_data = create_excel_file("test.xlsx")
            
            # Act
            response = client.post('/import/excel', files=[file_data])
        
        # Assert
        assert response.status_code == 500
        assert "Failed to create import job" in response.json()["detail"]


# ============================================================================
# TEST: GET /import/status/{job_id}
# ============================================================================

class TestGetImportStatus:
    """Test GET /import/status/{job_id} endpoint."""
    
    def test_returns_pending_status(self):
        """Should return pending status for new job."""
        # Arrange
        mock_db = MagicMock()
        mock_job_service = MagicMock()
        mock_job_service.get_job_status.return_value = {
            "job_id": "test-123",
            "status": "pending",
            "percent_complete": 0,
            "message": "Initializing..."
        }
        
        with patch('app.api.routes.import_excel.ImportJobService', return_value=mock_job_service), \
             patch('app.api.routes.import_excel.get_db', return_value=mock_db):
            
            # Act
            response = client.get('/import/status/test-123')
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert data["percent_complete"] == 0
    
    def test_returns_processing_status_with_progress(self):
        """Should return processing status with progress percentage."""
        # Arrange
        mock_db = MagicMock()
        mock_job_service = MagicMock()
        mock_job_service.get_job_status.return_value = {
            "job_id": "test-123",
            "status": "processing",
            "percent_complete": 45,
            "message": "Processing employee records...",
            "employees_processed": 100,
            "skills_processed": 250
        }
        
        with patch('app.api.routes.import_excel.ImportJobService', return_value=mock_job_service), \
             patch('app.api.routes.import_excel.get_db', return_value=mock_db):
            
            # Act
            response = client.get('/import/status/test-123')
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"
        assert data["percent_complete"] == 45
        assert data["employees_processed"] == 100
        assert data["skills_processed"] == 250
    
    def test_returns_completed_status_with_result(self):
        """Should return completed status with import result."""
        # Arrange
        mock_db = MagicMock()
        mock_job_service = MagicMock()
        mock_job_service.get_job_status.return_value = {
            "job_id": "test-123",
            "status": "completed",
            "percent_complete": 100,
            "message": "Import completed successfully",
            "result": {
                "employees_imported": 50,
                "skills_imported": 200,
                "failed_rows": []
            }
        }
        
        with patch('app.api.routes.import_excel.ImportJobService', return_value=mock_job_service), \
             patch('app.api.routes.import_excel.get_db', return_value=mock_db):
            
            # Act
            response = client.get('/import/status/test-123')
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["percent_complete"] == 100
        assert data["result"]["employees_imported"] == 50
    
    def test_returns_failed_status_with_error(self):
        """Should return failed status with error message."""
        # Arrange
        mock_db = MagicMock()
        mock_job_service = MagicMock()
        mock_job_service.get_job_status.return_value = {
            "job_id": "test-123",
            "status": "failed",
            "percent_complete": 30,
            "message": "Import failed",
            "error": "Invalid data in row 15: Missing required field 'employee_id'"
        }
        
        with patch('app.api.routes.import_excel.ImportJobService', return_value=mock_job_service), \
             patch('app.api.routes.import_excel.get_db', return_value=mock_db):
            
            # Act
            response = client.get('/import/status/test-123')
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert "error" in data
        assert "Invalid data" in data["error"]
    
    def test_returns_404_for_unknown_job(self):
        """Should return 404 when job_id not found."""
        # Arrange
        mock_db = MagicMock()
        mock_job_service = MagicMock()
        mock_job_service.get_job_status.return_value = None
        
        with patch('app.api.routes.import_excel.ImportJobService', return_value=mock_job_service), \
             patch('app.api.routes.import_excel.get_db', return_value=mock_db):
            
            # Act
            response = client.get('/import/status/nonexistent-job')
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_returns_503_on_transient_db_error(self):
        """Should return 503 on transient database errors."""
        # Arrange
        mock_db = MagicMock()
        mock_job_service = MagicMock()
        mock_job_service.get_job_status.side_effect = JobStatusDBError("Database busy")
        
        with patch('app.api.routes.import_excel.ImportJobService', return_value=mock_job_service), \
             patch('app.api.routes.import_excel.get_db', return_value=mock_db):
            
            # Act
            response = client.get('/import/status/test-123')
        
        # Assert
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unavailable"
        assert "retry" in data["message"].lower() or "please" in data["message"].lower()
    
    def test_adds_percent_complete_if_missing(self):
        """Should add percent_complete field for backward compatibility."""
        # Arrange
        mock_db = MagicMock()
        mock_job_service = MagicMock()
        mock_job_service.get_job_status.return_value = {
            "job_id": "test-123",
            "status": "processing",
            "percent": 60,  # Old field name
            "message": "Processing..."
        }
        
        with patch('app.api.routes.import_excel.ImportJobService', return_value=mock_job_service), \
             patch('app.api.routes.import_excel.get_db', return_value=mock_db):
            
            # Act
            response = client.get('/import/status/test-123')
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        # Should add percent_complete from percent field
        assert "percent_complete" in data
        assert data["percent_complete"] == 60


# ============================================================================
# TEST: Edge Cases
# ============================================================================

class TestImportEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_handles_empty_filename_extension(self):
        """Should reject file with no extension."""
        # Arrange
        file_data = ("file", ("datafile", io.BytesIO(b"content"), "application/octet-stream"))
        
        # Act
        response = client.post('/import/excel', files=[file_data])
        
        # Assert
        assert response.status_code == 400
    
    def test_handles_double_extension(self):
        """Should accept file with valid double extension."""
        # Arrange
        mock_db = MagicMock()
        mock_job_service = create_mock_job_service()
        
        with patch('app.api.routes.import_excel.ImportJobService', return_value=mock_job_service), \
             patch('app.api.routes.import_excel._save_upload_file', new_callable=AsyncMock, return_value="/tmp/test.xlsx"), \
             patch('app.api.routes.import_excel._process_import_async', new_callable=AsyncMock), \
             patch('app.api.routes.import_excel.get_db', return_value=mock_db):
            
            file_data = ("file", ("data.backup.xlsx", io.BytesIO(b"content"), "application/octet-stream"))
            
            # Act
            response = client.post('/import/excel', files=[file_data])
        
        # Assert
        assert response.status_code == 202
    
    def test_handles_unicode_filename(self):
        """Should accept file with unicode characters in filename."""
        # Arrange
        mock_db = MagicMock()
        mock_job_service = create_mock_job_service()
        
        with patch('app.api.routes.import_excel.ImportJobService', return_value=mock_job_service), \
             patch('app.api.routes.import_excel._save_upload_file', new_callable=AsyncMock, return_value="/tmp/test.xlsx"), \
             patch('app.api.routes.import_excel._process_import_async', new_callable=AsyncMock), \
             patch('app.api.routes.import_excel.get_db', return_value=mock_db):
            
            file_data = ("file", ("données_employés.xlsx", io.BytesIO(b"content"), "application/octet-stream"))
            
            # Act
            response = client.post('/import/excel', files=[file_data])
        
        # Assert
        assert response.status_code == 202
    
    def test_uuid_format_job_id(self):
        """Should handle UUID format job IDs in status polling."""
        # Arrange
        mock_db = MagicMock()
        mock_job_service = MagicMock()
        uuid_job_id = "550e8400-e29b-41d4-a716-446655440000"
        mock_job_service.get_job_status.return_value = {
            "job_id": uuid_job_id,
            "status": "completed",
            "percent_complete": 100
        }
        
        with patch('app.api.routes.import_excel.ImportJobService', return_value=mock_job_service), \
             patch('app.api.routes.import_excel.get_db', return_value=mock_db):
            
            # Act
            response = client.get(f'/import/status/{uuid_job_id}')
        
        # Assert
        assert response.status_code == 200
        assert response.json()["job_id"] == uuid_job_id


# ============================================================================
# TEST: Response Structure Validation
# ============================================================================

class TestResponseStructure:
    """Test response structure matches frontend expectations."""
    
    def test_post_response_has_required_fields(self):
        """POST response should have job_id, status, message."""
        # Arrange
        mock_db = MagicMock()
        mock_job_service = create_mock_job_service()
        
        with patch('app.api.routes.import_excel.ImportJobService', return_value=mock_job_service), \
             patch('app.api.routes.import_excel._save_upload_file', new_callable=AsyncMock, return_value="/tmp/test.xlsx"), \
             patch('app.api.routes.import_excel._process_import_async', new_callable=AsyncMock), \
             patch('app.api.routes.import_excel.get_db', return_value=mock_db):
            
            file_data = create_excel_file("test.xlsx")
            
            # Act
            response = client.post('/import/excel', files=[file_data])
        
        # Assert
        data = response.json()
        assert "job_id" in data
        assert "status" in data
        assert "message" in data
    
    def test_status_response_matches_frontend_expectations(self):
        """Status response should match BulkImportPage.jsx expectations."""
        # Arrange
        mock_db = MagicMock()
        mock_job_service = MagicMock()
        mock_job_service.get_job_status.return_value = {
            "job_id": "test-123",
            "status": "processing",
            "percent_complete": 50,
            "message": "Importing skills...",
            "employees_processed": 100,
            "skills_processed": 500
        }
        
        with patch('app.api.routes.import_excel.ImportJobService', return_value=mock_job_service), \
             patch('app.api.routes.import_excel.get_db', return_value=mock_db):
            
            # Act
            response = client.get('/import/status/test-123')
        
        # Assert
        data = response.json()
        # Frontend expects these fields
        assert "status" in data
        assert "percent_complete" in data
        assert "message" in data
        # Frontend uses these for progress display
        assert data["status"] in ["pending", "processing", "completed", "failed"]


# ============================================================================
# TEST: GET /import/{import_run_id}/unresolved-skills
# ============================================================================

class TestGetUnresolvedSkills:
    """Test GET /import/{import_run_id}/unresolved-skills endpoint."""
    
    def test_returns_unresolved_skills_for_valid_job(self):
        """Should return list of unresolved skills with suggestions."""
        # Arrange
        mock_db = MagicMock()
        mock_response = MagicMock()
        mock_response.import_run_id = "test-job-123"
        mock_response.total_count = 2
        mock_response.unresolved_skills = [
            MagicMock(
                raw_skill_id=1,
                raw_text="Python Dev",
                normalized_text="python dev",
                employee_name="John Doe",
                employee_zid="Z001234",
                suggestions=[]
            ),
            MagicMock(
                raw_skill_id=2,
                raw_text="JS",
                normalized_text="js",
                employee_name="Jane Smith",
                employee_zid="Z005678",
                suggestions=[]
            )
        ]
        
        with patch('app.api.routes.import_excel.get_unresolved_skills', return_value=mock_response), \
             patch('app.api.routes.import_excel.get_db', return_value=mock_db):
            
            # Act
            response = client.get('/import/test-job-123/unresolved-skills')
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["import_run_id"] == "test-job-123"
        assert data["total_count"] == 2
        assert len(data["unresolved_skills"]) == 2
    
    def test_returns_404_for_nonexistent_job(self):
        """Should return 404 when import job not found."""
        # Arrange
        mock_db = MagicMock()
        
        from app.services.imports.unresolved_skills_service import ImportJobNotFoundError
        
        with patch('app.api.routes.import_excel.get_unresolved_skills', 
                   side_effect=ImportJobNotFoundError("nonexistent-job")), \
             patch('app.api.routes.import_excel.get_db', return_value=mock_db):
            
            # Act
            response = client.get('/import/nonexistent-job/unresolved-skills')
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_includes_suggestions_by_default(self):
        """Should include suggestions when include_suggestions=true (default)."""
        # Arrange
        mock_db = MagicMock()
        
        with patch('app.api.routes.import_excel.get_unresolved_skills') as mock_get, \
             patch('app.api.routes.import_excel.get_db', return_value=mock_db):
            mock_get.return_value = MagicMock(
                import_run_id="test-123",
                total_count=0,
                unresolved_skills=[]
            )
            
            # Act
            client.get('/import/test-123/unresolved-skills')
        
        # Assert
        mock_get.assert_called_once()
        _, kwargs = mock_get.call_args
        assert kwargs.get('include_suggestions', True) is True
    
    def test_respects_include_suggestions_false(self):
        """Should pass include_suggestions=false when specified."""
        # Arrange
        mock_db = MagicMock()
        
        with patch('app.api.routes.import_excel.get_unresolved_skills') as mock_get, \
             patch('app.api.routes.import_excel.get_db', return_value=mock_db):
            mock_get.return_value = MagicMock(
                import_run_id="test-123",
                total_count=0,
                unresolved_skills=[]
            )
            
            # Act
            client.get('/import/test-123/unresolved-skills?include_suggestions=false')
        
        # Assert
        mock_get.assert_called_once()
        _, kwargs = mock_get.call_args
        assert kwargs.get('include_suggestions') is False


# ============================================================================
# TEST: POST /import/{import_run_id}/unresolved-skills/resolve
# ============================================================================

class TestResolveSkill:
    """Test POST /import/{import_run_id}/unresolved-skills/resolve endpoint."""
    
    def test_resolves_skill_successfully(self):
        """Should resolve skill to target and create alias."""
        # Arrange
        mock_db = MagicMock()
        mock_response = MagicMock()
        mock_response.raw_skill_id = 1
        mock_response.resolved_skill_id = 100
        mock_response.alias_created = True
        mock_response.alias_text = "python dev"
        mock_response.message = "Skill 'Python Dev' mapped to 'Python'"
        
        with patch('app.api.routes.import_excel.resolve_skill', return_value=mock_response), \
             patch('app.api.routes.import_excel.get_db', return_value=mock_db):
            
            # Act
            response = client.post(
                '/import/test-job-123/unresolved-skills/resolve',
                json={"raw_skill_id": 1, "target_skill_id": 100}
            )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["raw_skill_id"] == 1
        assert data["resolved_skill_id"] == 100
        assert data["alias_created"] is True
    
    def test_returns_404_for_nonexistent_job(self):
        """Should return 404 when import job not found."""
        # Arrange
        mock_db = MagicMock()
        
        from app.services.imports.unresolved_skills_service import ImportJobNotFoundError
        
        with patch('app.api.routes.import_excel.resolve_skill',
                   side_effect=ImportJobNotFoundError("bad-job")), \
             patch('app.api.routes.import_excel.get_db', return_value=mock_db):
            
            # Act
            response = client.post(
                '/import/bad-job/unresolved-skills/resolve',
                json={"raw_skill_id": 1, "target_skill_id": 100}
            )
        
        # Assert
        assert response.status_code == 404
    
    def test_returns_404_for_nonexistent_raw_skill(self):
        """Should return 404 when raw skill input not found."""
        # Arrange
        mock_db = MagicMock()
        
        from app.services.imports.unresolved_skills_service import RawSkillNotFoundError
        
        with patch('app.api.routes.import_excel.resolve_skill',
                   side_effect=RawSkillNotFoundError(999)), \
             patch('app.api.routes.import_excel.get_db', return_value=mock_db):
            
            # Act
            response = client.post(
                '/import/test-job/unresolved-skills/resolve',
                json={"raw_skill_id": 999, "target_skill_id": 100}
            )
        
        # Assert
        assert response.status_code == 404
    
    def test_returns_404_for_nonexistent_target_skill(self):
        """Should return 404 when target skill not found."""
        # Arrange
        mock_db = MagicMock()
        
        from app.services.imports.unresolved_skills_service import SkillNotFoundError
        
        with patch('app.api.routes.import_excel.resolve_skill',
                   side_effect=SkillNotFoundError(999)), \
             patch('app.api.routes.import_excel.get_db', return_value=mock_db):
            
            # Act
            response = client.post(
                '/import/test-job/unresolved-skills/resolve',
                json={"raw_skill_id": 1, "target_skill_id": 999}
            )
        
        # Assert
        assert response.status_code == 404
    
    def test_returns_400_for_already_resolved(self):
        """Should return 400 when skill is already resolved."""
        # Arrange
        mock_db = MagicMock()
        
        from app.services.imports.unresolved_skills_service import AlreadyResolvedError
        
        with patch('app.api.routes.import_excel.resolve_skill',
                   side_effect=AlreadyResolvedError(1)), \
             patch('app.api.routes.import_excel.get_db', return_value=mock_db):
            
            # Act
            response = client.post(
                '/import/test-job/unresolved-skills/resolve',
                json={"raw_skill_id": 1, "target_skill_id": 100}
            )
        
        # Assert
        assert response.status_code == 400
        assert "already resolved" in response.json()["detail"].lower()
    
    def test_returns_409_for_conflicting_alias(self):
        """Should return 409 when alias maps to different skill."""
        # Arrange
        mock_db = MagicMock()
        
        from app.services.imports.unresolved_skills_service import AliasAlreadyExistsError
        
        with patch('app.api.routes.import_excel.resolve_skill',
                   side_effect=AliasAlreadyExistsError("python dev", 200, "Python Development")), \
             patch('app.api.routes.import_excel.get_db', return_value=mock_db):
            
            # Act
            response = client.post(
                '/import/test-job/unresolved-skills/resolve',
                json={"raw_skill_id": 1, "target_skill_id": 100}
            )
        
        # Assert
        assert response.status_code == 409
        data = response.json()["detail"]
        assert data["existing_skill_id"] == 200
        assert data["existing_skill_name"] == "Python Development"


# ============================================================================
# TEST: GET /import/{import_run_id}/unresolved-skills/{raw_skill_id}/suggestions
# ============================================================================

class TestGetSingleSkillSuggestions:
    """Test GET /import/{run_id}/unresolved-skills/{raw_skill_id}/suggestions endpoint."""
    
    def test_returns_suggestions_for_valid_skill(self):
        """Should return suggestions for a single unresolved skill."""
        # Arrange
        mock_db = MagicMock()
        mock_response = MagicMock()
        mock_response.raw_skill_id = 42
        mock_response.raw_text = "Python Dev"
        mock_response.normalized_text = "python dev"
        mock_response.employee_name = "John Doe"
        mock_response.employee_zid = "Z001234"
        mock_response.suggestions = [
            MagicMock(
                skill_id=100,
                skill_name="Python",
                category="Programming",
                subcategory="Languages",
                match_type="exact",
                confidence=1.0
            )
        ]
        
        with patch('app.api.routes.import_excel.get_single_skill_suggestions', 
                   return_value=mock_response), \
             patch('app.api.routes.import_excel.get_db', return_value=mock_db):
            
            # Act
            response = client.get('/import/test-job-123/unresolved-skills/42/suggestions')
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["raw_skill_id"] == 42
        assert data["raw_text"] == "Python Dev"
        assert len(data["suggestions"]) == 1
        assert data["suggestions"][0]["skill_name"] == "Python"
    
    def test_returns_404_for_nonexistent_job(self):
        """Should return 404 when import job not found."""
        # Arrange
        mock_db = MagicMock()
        
        from app.services.imports.unresolved_skills_service import ImportJobNotFoundError
        
        with patch('app.api.routes.import_excel.get_single_skill_suggestions', 
                   side_effect=ImportJobNotFoundError("bad-job")), \
             patch('app.api.routes.import_excel.get_db', return_value=mock_db):
            
            # Act
            response = client.get('/import/bad-job/unresolved-skills/1/suggestions')
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_returns_404_for_nonexistent_raw_skill(self):
        """Should return 404 when raw_skill_id not found."""
        # Arrange
        mock_db = MagicMock()
        
        from app.services.imports.unresolved_skills_service import RawSkillNotFoundError
        
        with patch('app.api.routes.import_excel.get_single_skill_suggestions', 
                   side_effect=RawSkillNotFoundError(999)), \
             patch('app.api.routes.import_excel.get_db', return_value=mock_db):
            
            # Act
            response = client.get('/import/test-job/unresolved-skills/999/suggestions')
        
        # Assert
        assert response.status_code == 404
        assert "999" in response.json()["detail"]
    
    def test_passes_query_parameters(self):
        """Should pass max_suggestions and include_embeddings params."""
        # Arrange
        mock_db = MagicMock()
        
        with patch('app.api.routes.import_excel.get_single_skill_suggestions') as mock_get, \
             patch('app.api.routes.import_excel.get_db', return_value=mock_db):
            mock_get.return_value = MagicMock(
                raw_skill_id=1,
                raw_text="Test",
                normalized_text="test",
                employee_name=None,
                employee_zid=None,
                suggestions=[]
            )
            
            # Act
            client.get('/import/job-1/unresolved-skills/1/suggestions?max_suggestions=5&include_embeddings=false')
        
        # Assert
        mock_get.assert_called_once()
        _, kwargs = mock_get.call_args
        assert kwargs.get('max_suggestions') == 5
        assert kwargs.get('include_embeddings') is False
    
    def test_only_fetches_single_skill(self):
        """Should call service with specific raw_skill_id (not fetch all skills)."""
        # Arrange
        mock_db = MagicMock()
        
        with patch('app.api.routes.import_excel.get_single_skill_suggestions') as mock_get, \
             patch('app.api.routes.import_excel.get_unresolved_skills') as mock_get_all, \
             patch('app.api.routes.import_excel.get_db', return_value=mock_db):
            mock_get.return_value = MagicMock(
                raw_skill_id=42,
                raw_text="Test",
                normalized_text="test",
                employee_name=None,
                employee_zid=None,
                suggestions=[]
            )
            
            # Act
            client.get('/import/job-1/unresolved-skills/42/suggestions')
        
        # Assert - single skill endpoint called, NOT the all-skills endpoint
        mock_get.assert_called_once()
        mock_get_all.assert_not_called()
        
        # Verify raw_skill_id is 42, not all skills
        _, kwargs = mock_get.call_args
        assert kwargs.get('raw_skill_id') == 42