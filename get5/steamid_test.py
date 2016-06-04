import unittest

import steamid
import get5_test


class SteamIdTests(get5_test.Get5Test):

    def test_auth_to_steam64(self):
        input = 'STEAM_0:1:52245092'
        expected = '76561198064755913'
        suc, actual = steamid.auth_to_steam64(input)
        self.assertTrue(suc)
        self.assertEqual(actual, expected)

        input = 'STEAM_1:1:52245092'
        expected = '76561198064755913'
        suc, actual = steamid.auth_to_steam64(input)
        self.assertTrue(suc)
        self.assertEqual(actual, expected)

        input = '76561198064755913'
        expected = '76561198064755913'
        suc, actual = steamid.auth_to_steam64(input)
        self.assertTrue(suc)
        self.assertEqual(actual, expected)

        input = '1:1:52245092'
        expected = '76561198064755913'
        suc, actual = steamid.auth_to_steam64(input)
        self.assertTrue(suc)
        self.assertEqual(actual, expected)

        input = '[U:1:104490185]'
        expected = '76561198064755913'
        suc, actual = steamid.auth_to_steam64(input)
        self.assertTrue(suc)
        self.assertEqual(actual, expected)

        input = 'steamcommunity.com/profiles/76561198064755913'
        expected = '76561198064755913'
        suc, actual = steamid.auth_to_steam64(input)
        self.assertTrue(suc)
        self.assertEqual(actual, expected)

        input = 'http://steamcommunity.com/profiles/76561198064755913'
        expected = '76561198064755913'
        suc, actual = steamid.auth_to_steam64(input)
        self.assertTrue(suc)
        self.assertEqual(actual, expected)

        input = 'http://steamcommunity.com/profiles/76561198064755913/'
        expected = '76561198064755913'
        suc, actual = steamid.auth_to_steam64(input)
        self.assertTrue(suc)
        self.assertEqual(actual, expected)

        input = 'http://steamcommunity.com/id/splewis'
        expected = '76561198064755913'
        suc, actual = steamid.auth_to_steam64(input)
        self.assertTrue(suc)
        self.assertEqual(actual, expected)

        input = 'http://steamcommunity.com/id/splewis2'
        expected = ''
        suc, actual = steamid.auth_to_steam64(input)
        self.assertFalse(suc)
        self.assertEqual(actual, expected)

        input = 'splewis'
        expected = '76561198064755913'
        suc, actual = steamid.auth_to_steam64(input)
        self.assertTrue(suc)
        self.assertEqual(actual, expected)

        input = 'splewis_bad'
        expected = ''
        suc, actual = steamid.auth_to_steam64(input)
        self.assertFalse(suc)
        self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()
