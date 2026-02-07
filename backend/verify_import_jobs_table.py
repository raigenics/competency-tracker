"""
Verification script to test the import_jobs table.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text
from app.db.session import SessionLocal
from app.models.import_job import ImportJob
import uuid


def verify_import_jobs_table():
    """Verify the import_jobs table exists and works."""
    print("🔍 Verifying import_jobs table...")
    
    db = SessionLocal()
    try:
        # Test 1: Check if table exists
        print("\n✅ Test 1: Checking if table exists...")
        result = db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'import_jobs'
        """))
        if result.fetchone():
            print("   ✓ Table 'import_jobs' exists")
        else:
            print("   ✗ Table 'import_jobs' does NOT exist")
            return False
        
        # Test 2: Check table structure
        print("\n✅ Test 2: Checking table structure...")
        result = db.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'import_jobs'
            ORDER BY ordinal_position
        """))
        columns = result.fetchall()
        print(f"   Found {len(columns)} columns:")
        for col in columns:
            print(f"   - {col[0]}: {col[1]} (nullable: {col[2]})")
        
        # Test 3: Insert a test job using the model
        print("\n✅ Test 3: Creating a test import job...")
        test_job = ImportJob(
            job_id=str(uuid.uuid4()),
            status='processing',
            message='Test job',
            total_rows=100,
            processed_rows=50,
            percent_complete=50,
            employees_total=100,
            employees_processed=50,
            skills_total=500,
            skills_processed=250
        )
        db.add(test_job)
        db.commit()
        db.refresh(test_job)
        print(f"   ✓ Created job: {test_job}")
        
        # Test 4: Query the job back
        print("\n✅ Test 4: Querying the test job...")
        queried_job = db.query(ImportJob).filter_by(job_id=test_job.job_id).first()
        if queried_job:
            print(f"   ✓ Found job: {queried_job}")
            print(f"   ✓ Status: {queried_job.status}")
            print(f"   ✓ Progress: {queried_job.percent_complete}%")
        else:
            print("   ✗ Could not query job back")
            return False
        
        # Test 5: Test to_dict() method
        print("\n✅ Test 5: Testing to_dict() method...")
        job_dict = queried_job.to_dict()
        print(f"   ✓ Dictionary keys: {list(job_dict.keys())}")
        print(f"   ✓ job_id: {job_dict['job_id']}")
        print(f"   ✓ status: {job_dict['status']}")
        print(f"   ✓ percent_complete: {job_dict['percent_complete']}")
        
        # Test 6: Update the job
        print("\n✅ Test 6: Updating the job...")
        queried_job.processed_rows = 75
        queried_job.percent_complete = 75
        queried_job.message = "Updated message"
        db.commit()
        db.refresh(queried_job)
        print(f"   ✓ Updated progress to {queried_job.percent_complete}%")
        
        # Test 7: Complete the job
        print("\n✅ Test 7: Completing the job...")
        from datetime import datetime, timezone
        queried_job.status = 'completed'
        queried_job.percent_complete = 100
        queried_job.processed_rows = 100
        queried_job.completed_at = datetime.now(timezone.utc)
        queried_job.result = {
            'employees_imported': 100,
            'skills_imported': 500,
            'warnings': []
        }
        db.commit()
        db.refresh(queried_job)
        print(f"   ✓ Job completed at: {queried_job.completed_at}")
        print(f"   ✓ Result: {queried_job.result}")
        
        # Test 8: Clean up
        print("\n✅ Test 8: Cleaning up test data...")
        db.delete(queried_job)
        db.commit()
        print("   ✓ Test job deleted")
        
        print("\n" + "="*60)
        print("🎉 ALL TESTS PASSED! The import_jobs table is working correctly.")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = verify_import_jobs_table()
    sys.exit(0 if success else 1)
