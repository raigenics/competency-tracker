#!/usr/bin/env python
"""Test if app.main can be imported."""
try:
    import app.main
    print("✅ SUCCESS: app.main imported successfully")
    print(f"✅ FastAPI app object found: {hasattr(app.main, 'app')}")
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
