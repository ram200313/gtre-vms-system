import os
import sys
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"Starting VMS Cloud Instance on Port {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port)
