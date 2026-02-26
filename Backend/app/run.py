import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Test your imports
from Backend.app.core.database import Base
print("Database Base imported OK")

# Or run main
# from Backend.app.main import app  # adjust if you have main.py
