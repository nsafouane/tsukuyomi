import sys
import os
import asyncio

# Add project root to path
sys.path.append("/root/.openclaw/workspace/tsukuyomi")

async def test_os():
    print(f"OS imported: {os}")
    try:
        # Simulate the line that fails
        path = os.path.join(os.getcwd(), "test")
        print(f"Path join success: {path}")
    except Exception as e:
        print(f"Failed with: {e}")

if __name__ == "__main__":
    asyncio.run(test_os())
