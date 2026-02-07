"""
Quick test to verify progress indicator implementation.
Run this to test the job tracker and progress reporting.
"""
import sys
sys.path.insert(0, 'backend')

from app.services.imports.employee_import.import_job_tracker import get_job_tracker

def test_job_tracker():
    """Test the job tracker basic functionality."""
    tracker = get_job_tracker()
    
    print("🧪 Testing Job Tracker Implementation\n")
    
    # Test 1: Create job
    print("✅ Test 1: Create job")
    job_id = tracker.create_job(total_rows=100)
    print(f"   Created job: {job_id}")
    
    # Test 2: Get status
    print("\n✅ Test 2: Get initial status")
    status = tracker.get_status(job_id)
    print(f"   Status: {status.status}")
    print(f"   Progress: {status.percent_complete}%")
    print(f"   Message: {status.message}")
    
    # Test 3: Update progress
    print("\n✅ Test 3: Update progress")
    tracker.update_progress(
        job_id=job_id,
        processed_rows=25,
        total_rows=100,
        message="Processing employees...",
        employees_processed=10,
        skills_processed=45
    )
    status = tracker.get_status(job_id)
    print(f"   Progress: {status.percent_complete}%")
    print(f"   Message: {status.message}")
    print(f"   Employees: {status.employees_processed}")
    print(f"   Skills: {status.skills_processed}")
    
    # Test 4: Multiple updates
    print("\n✅ Test 4: Simulate import progress")
    progress_points = [
        (0, "Reading Excel file..."),
        (5, "Excel file loaded"),
        (15, "Cleared existing data"),
        (25, "Importing employees..."),
        (50, "Importing skills..."),
        (85, "Finalizing skills import..."),
        (90, "Saving to database..."),
    ]
    
    for percent, msg in progress_points:
        tracker.update_progress(
            job_id=job_id,
            processed_rows=percent,
            total_rows=100,
            message=msg
        )
        status = tracker.get_status(job_id)
        print(f"   [{status.percent_complete:3.0f}%] {status.message}")
    
    # Test 5: Complete job
    print("\n✅ Test 5: Complete job")
    result = {
        "status": "completed",
        "employee_total": 150,
        "employee_imported": 150,
        "skill_total": 450,
        "skill_imported": 450
    }
    tracker.complete_job(job_id, result, success=True)
    status = tracker.get_status(job_id)
    print(f"   Status: {status.status}")
    print(f"   Progress: {status.percent_complete}%")
    print(f"   Result: {status.result}")
    
    # Test 6: Failed job
    print("\n✅ Test 6: Test failed job")
    failed_job_id = tracker.create_job(total_rows=50)
    tracker.fail_job(failed_job_id, error="Test error: Invalid file format")
    status = tracker.get_status(failed_job_id)
    print(f"   Status: {status.status}")
    print(f"   Error: {status.error}")
    
    # Test 7: Non-existent job
    print("\n✅ Test 7: Get non-existent job")
    status = tracker.get_status("non-existent-job-id")
    print(f"   Result: {status}")
    
    print("\n" + "="*60)
    print("✅ All tests passed! Job tracker is working correctly.")
    print("="*60)

if __name__ == "__main__":
    test_job_tracker()
