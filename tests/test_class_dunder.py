import unittest
import os
import sys
#Import cspc_api using the directory one level up as root
path = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(path)
from cspc_api import CspcApi

class Test_Dunders(unittest.TestCase):
    def test__eq__(self):
        """tests the dunder equal method."""
        assert CspcApi("1.1.1.1", "user", "pw", True) == CspcApi("1.1.1.1", "user", "pw", True)

    def test__str__(self):
        """tests the dunder str method."""
        assert str(CspcApi("1.1.1.1", "user", "pw", True)) == 'CspcApi("1.1.1.1", "user", "pw", True)'
if __name__ == '__main__':
    unittest.main()
