import os
import sys
import traceback
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"Starting VMS Cloud Instance on Port {port}")
    sys.stdout.flush()
    try:
        from main import app
        uvicorn.run("main:app", host="0.0.0.0", port=port)
    except Exception as e:
        print("\n\n=== EXTREME CRASH DIAGNOSTICS ===")
        traceback.print_exc(file=sys.stdout)
        print("=================================\n\n")
        sys.stdout.flush()
        sys.exit(1)
