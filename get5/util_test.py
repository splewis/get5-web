import unittest

import util
import get5_test


class UtilTest(get5_test.Get5Test):

    def test_as_int(self):
        self.assertEqual(util.as_int('abcdef'), 0)
        self.assertEqual(util.as_int('3'), 3)

    def test_format_mapname(self):
        self.assertEqual(util.format_mapname('de_inferno'), 'Inferno')
        self.assertEqual(util.format_mapname('de_test'), 'Test')
        self.assertEqual(util.format_mapname('de_dust2'), 'Dust II')
        self.assertEqual(util.format_mapname('de_cbble'), 'Cobblestone')


if __name__ == '__main__':
    unittest.main()
