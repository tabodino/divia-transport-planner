"""
Pytest configuration for the DiviaMobilités Transport Planner project.

This file automatically sets up the PYTHONPATH so that imports
from the src directory work correctly in the tests.
"""

import sys
from pathlib import Path

# Add project root directory on PYTHONPATH
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
