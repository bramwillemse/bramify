"""Patch module imports for testing."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

# Absolute path naar src directory
SRC_DIR = Path(__file__).parent.parent / 'src'

# De modules die gepatcht moeten worden
MODULES_TO_PATCH = {
    'plugins.plugin_base': f'{SRC_DIR}/plugins/plugin_base.py',
    'plugins': f'{SRC_DIR}/plugins',
    'integrations.google_sheets.client': f'{SRC_DIR}/integrations/google_sheets/client.py',
    'integrations.telegram.utils': f'{SRC_DIR}/integrations/telegram/utils.py',
    'utils.date_utils': f'{SRC_DIR}/utils/date_utils.py',
}

# Functie om modules te patchen
def patch_imports():
    """Patch imports voor test doeleinden."""
    for module_name, module_path in MODULES_TO_PATCH.items():
        if module_name not in sys.modules:
            sys.modules[module_name] = MagicMock()
            
    # Voeg src directory toe aan sys.path
    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))
    if str(SRC_DIR.parent) not in sys.path:
        sys.path.insert(0, str(SRC_DIR.parent))