import unittest

import get5_test
from countries import get_flag_img_path, valid_country, country_name


class ApiTests(get5_test.Get5Test):

    def test_get_flag_img_path(self):
        self.assertEqual(get_flag_img_path(
            'us'), '/static/img/valve_flags/us.png')
        self.assertEqual(get_flag_img_path(
            'US'), '/static/img/valve_flags/us.png')
        self.assertEqual(get_flag_img_path(
            'fr'), '/static/img/valve_flags/fr.png')
        self.assertEqual(get_flag_img_path(
            'FR'), '/static/img/valve_flags/fr.png')
        self.assertEqual(get_flag_img_path('f'), '/static/img/_unknown.png')
        self.assertEqual(get_flag_img_path(''), '/static/img/_unknown.png')

    def test_valid_country(self):
        self.assertEqual(valid_country('us'), True)
        self.assertEqual(valid_country('US'), True)
        self.assertEqual(valid_country('fr'), True)
        self.assertEqual(valid_country('FR'), True)
        self.assertEqual(valid_country('f'), False)
        self.assertEqual(valid_country(''), False)

    def test_country_name(self):
        self.assertEqual(country_name('us'), 'United States')
        self.assertEqual(country_name('US'), 'United States')
        self.assertEqual(country_name('fr'), 'France')
        self.assertEqual(country_name('FR'), 'France')
        self.assertEqual(country_name('f'), None)
        self.assertEqual(country_name(''), None)


if __name__ == '__main__':
    unittest.main()
