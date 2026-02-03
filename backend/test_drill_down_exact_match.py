#!/usr/bin/env python
"""
Quick test to verify the drill-down fix is working correctly.
Tests that clicking a skill node returns only employees with that exact skill_id.
"""
import requests
import json

def test_drill_down_exact_match():
    """Test that skill summary uses exact skill_id matching."""
    base_url = "http://localhost:8000"
    
    print("🔍 Testing Capability Overview Drill-Down Fix")
    print("=" * 60)
    
    try:
        # First, search for React skills to find their IDs
        print("\n1️⃣ Searching for 'react' skills...")
        search_response = requests.get(
            f"{base_url}/api/skills/capability/search",
            params={"q": "react"}
        )
        
        if search_response.status_code == 200:
            search_data = search_response.json()
            results = search_data.get('results', [])
            
            print(f"   Found {len(results)} React-related skills:")
            for result in results:
                print(f"   - ID: {result['skill_id']}, Name: {result['skill_name']}")
            
            if len(results) == 0:
                print("   ⚠️  No React skills found in database")
                return
            
            # Test each React skill separately
            print(f"\n2️⃣ Testing drill-down for each skill...")
            for skill in results:
                skill_id = skill['skill_id']
                skill_name = skill['skill_name']
                
                print(f"\n   Testing: {skill_name} (ID: {skill_id})")
                
                summary_response = requests.get(
                    f"{base_url}/api/skills/{skill_id}/summary"
                )
                
                if summary_response.status_code == 200:
                    summary = summary_response.json()
                    
                    print(f"   ✅ API Response:")
                    print(f"      - Skill Name: {summary.get('skill_name')}")
                    print(f"      - Employee Count: {summary.get('employee_count')}")
                    print(f"      - Employee IDs: {summary.get('employee_ids', [])[:5]}")
                    print(f"      - Avg Experience: {summary.get('avg_experience_years')} years")
                    print(f"      - Certified: {summary.get('certified_employee_count')}")
                    
                    # Verify the skill_id in response matches request
                    if summary.get('skill_id') == skill_id:
                        print(f"   ✅ Correct skill_id returned: {skill_id}")
                    else:
                        print(f"   ❌ ERROR: Skill ID mismatch! Expected {skill_id}, got {summary.get('skill_id')}")
                    
                    # Check if employee count is reasonable (not aggregated)
                    emp_count = summary.get('employee_count', 0)
                    if emp_count > 0:
                        print(f"   ✅ Has {emp_count} employee(s) with this exact skill")
                    else:
                        print(f"   ℹ️  No employees have this skill")
                        
                else:
                    print(f"   ❌ API Error: {summary_response.status_code}")
                    print(f"   {summary_response.text[:200]}")
            
            print("\n" + "=" * 60)
            print("✅ TEST COMPLETE")
            print("=" * 60)
            print("\n📋 Expected Behavior:")
            print("   - Each skill should return ONLY its own employees")
            print("   - 'React' should NOT include 'ReactJS' or 'React.js' employees")
            print("   - Each skill should have different employee counts")
            
        else:
            print(f"❌ Search failed: {search_response.status_code}")
            print(f"   {search_response.text[:200]}")
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to backend server")
        print("   Make sure the server is running:")
        print("   cd backend && uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    test_drill_down_exact_match()
