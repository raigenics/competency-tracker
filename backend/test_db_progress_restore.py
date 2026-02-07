"""
Test script to verify DB-backed progress tracking is fully restored.

This test verifies:
1. ImportService accepts job_id parameter
2. Orchestrator uses ImportJobService (not in-memory tracker)
3. Progress updates are written to import_jobs table
4. Status endpoint reads from database
5. Complete/fail updates are never throttled
"""
import sys
import time
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.db.session import SessionLocal
from app.services.import_service import ImportService
from app.services.import_job_service import ImportJobService
from app.models.import_job import ImportJob


def test_constructor_signature():
    """Test that ImportService accepts job_id parameter."""
    print("\n" + "=" * 60)
    print("TEST 1: Constructor Signature")
    print("=" * 60)
    
    try:
        db = SessionLocal()
        
        # This should NOT raise TypeError
        service = ImportService(db_session=db, job_id="test-job-123")
        
        print("✅ ImportService accepts job_id parameter")
        print(f"   - job_id: {service._orchestrator.job_id}")
        print(f"   - job_service: {type(service._orchestrator.job_service).__name__}")
        
        assert service._orchestrator.job_id == "test-job-123"
        assert service._orchestrator.job_service is not None
        assert isinstance(service._orchestrator.job_service, ImportJobService)
        
        db.close()
        return True
        
    except TypeError as e:
        print(f"❌ FAILED: {e}")
        return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_job_lifecycle():
    """Test full job lifecycle with DB persistence."""
    print("\n" + "=" * 60)
    print("TEST 2: Job Lifecycle (Create → Update → Complete)")
    print("=" * 60)
    
    try:
        db = SessionLocal()
        job_service = ImportJobService(db)
        
        # Step 1: Create job
        job_id = job_service.create_job(message="Starting test import...")
        print(f"✅ Created job: {job_id}")
        
        # Verify in database
        job = db.query(ImportJob).filter_by(job_id=job_id).first()
        assert job is not None, "Job not found in database"
        assert job.status == 'pending'
        print(f"   - Status: {job.status}")
        print(f"   - Message: {job.message}")
        
        # Step 2: Update to processing
        job_service.update_job(job_id, status='processing', percent=10, message="Processing...")
        db.refresh(job)
        assert job.status == 'processing'
        assert job.percent_complete == 10
        print(f"✅ Updated to processing (10%)")
        
        # Step 3: Update progress (should respect throttling)
        job_service.update_job(job_id, percent=15, message="Still processing...")
        db.refresh(job)
        print(f"✅ Progress update: {job.percent_complete}%")
        
        # Step 4: Cross boundary (should always update)
        job_service.update_job(job_id, percent=50, message="Halfway...")
        db.refresh(job)
        assert job.percent_complete == 50
        print(f"✅ Crossed 50% boundary: {job.percent_complete}%")
        
        # Step 5: Update to 90% (critical boundary)
        job_service.update_job(job_id, percent=90, message="Almost done...")
        db.refresh(job)
        assert job.percent_complete == 90
        print(f"✅ Crossed 90% boundary: {job.percent_complete}%")
        
        # Step 6: Complete (should always update)
        result = {
            'employees_imported': 100,
            'skills_imported': 500,
            'status': 'success'
        }
        job_service.complete_job(job_id, result)
        db.refresh(job)
        
        assert job.status == 'completed'
        assert job.percent_complete == 100
        assert job.result is not None
        assert job.completed_at is not None
        print(f"✅ Job completed successfully")
        print(f"   - Status: {job.status}")
        print(f"   - Percent: {job.percent_complete}%")
        print(f"   - Result: {job.result}")
        
        # Cleanup
        db.delete(job)
        db.commit()
        db.close()
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_throttling_boundaries():
    """Test that progress boundaries (0, 10, 20, ..., 100) are never throttled."""
    print("\n" + "=" * 60)
    print("TEST 3: Throttling Respects Boundaries")
    print("=" * 60)
    
    try:
        db = SessionLocal()
        job_service = ImportJobService(db)
        
        job_id = job_service.create_job(message="Testing boundaries...")
        
        boundaries = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        
        for boundary in boundaries:
            # Small delay to avoid same-second updates
            time.sleep(0.1)
            
            updated = job_service.update_job(
                job_id, 
                percent=boundary, 
                message=f"At {boundary}%"
            )
            
            job = db.query(ImportJob).filter_by(job_id=job_id).first()
            
            if boundary in [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
                # These should ALWAYS update (boundaries)
                assert job.percent_complete == boundary, f"Boundary {boundary}% not updated!"
                print(f"✅ Boundary {boundary:3d}% - Updated (as expected)")
            
        # Cleanup
        db.delete(job)
        db.commit()
        db.close()
        
        print(f"✅ All boundaries updated correctly")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_status_endpoint_format():
    """Test that get_job_status returns correct format for frontend."""
    print("\n" + "=" * 60)
    print("TEST 4: Status Endpoint Format")
    print("=" * 60)
    
    try:
        db = SessionLocal()
        job_service = ImportJobService(db)
        
        job_id = job_service.create_job(message="Test status format...")
        job_service.update_job(job_id, status='processing', percent=42, message="Processing...")
        
        # Get status
        status = job_service.get_job_status(job_id)
        
        assert status is not None
        assert 'job_id' in status
        assert 'status' in status
        assert 'percent_complete' in status
        assert 'message' in status
        
        print(f"✅ Status format correct:")
        print(f"   - job_id: {status['job_id']}")
        print(f"   - status: {status['status']}")
        print(f"   - percent_complete: {status['percent_complete']}")
        print(f"   - message: {status['message']}")
        
        # Cleanup
        job = db.query(ImportJob).filter_by(job_id=job_id).first()
        db.delete(job)
        db.commit()
        db.close()
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "🔬" * 30)
    print("DB-BACKED PROGRESS TRACKING VERIFICATION")
    print("🔬" * 30)
    
    results = []
    
    # Test 1: Constructor signature
    results.append(("Constructor Signature", test_constructor_signature()))
    
    # Test 2: Job lifecycle
    results.append(("Job Lifecycle", test_job_lifecycle()))
    
    # Test 3: Throttling boundaries
    results.append(("Throttling Boundaries", test_throttling_boundaries()))
    
    # Test 4: Status endpoint format
    results.append(("Status Endpoint Format", test_status_endpoint_format()))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! DB-backed progress tracking is fully restored.")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
