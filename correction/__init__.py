import sys
import importlib.util

# List of necessary packages for correction
__necessary_correction_packages = [
    "cupy"
        ]

# Checks if all packages are installed
for packageName in __necessary_correction_packages:
    if not packageName in sys.modules and importlib.util.find_spec(packageName) is None: 
        raise Exception(f"Dependencies for correction not installed. Please verify if the following modules are correctly installed: {__necessary_correction_packages}")
