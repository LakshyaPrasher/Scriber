"""Tests for Single Instance enforcement in Scriber Studio."""

import unittest
from unittest.mock import patch, MagicMock
import sys

from scriber.single_instance import ensure_single_instance, release_single_instance


class TestSingleInstance(unittest.TestCase):
    """Verifies that duplicate instances are blocked cleanly."""

    def test_single_instance_primary(self):
        """First invocation should succeed."""
        try:
            # First acquisition should return True
            res = ensure_single_instance()
            self.assertTrue(res)
        finally:
            release_single_instance()

    @patch("ctypes.windll.kernel32.GetLastError")
    def test_single_instance_duplicate_blocked(self, mock_get_last_error):
        """Simulate ERROR_ALREADY_EXISTS (183). Should return False."""
        if sys.platform != "win32":
            self.skipTest("Windows-only mutex test")

        mock_get_last_error.return_value = 183  # ERROR_ALREADY_EXISTS
        with patch("scriber.single_instance.focus_existing_window") as mock_focus:
            mock_focus.return_value = True
            res = ensure_single_instance()
            self.assertFalse(res, "Duplicate instance must return False")
            mock_focus.assert_called_once()
        release_single_instance()


if __name__ == "__main__":
    unittest.main()
