import unittest

import get5_test
from flask import url_for
from models import User, Match, GameServer


class MatchTests(get5_test.Get5Test):

    def test_render_pages_loggedin(self):
        with self.app as c:
            with c.session_transaction() as sess:
                sess['user_id'] = 1
            self.assertEqual(self.app.get('/matches').status_code, 200)
            self.assertEqual(self.app.get('/matches/1').status_code, 200)

    def test_render_pages_not_loggedin(self):
        self.assertEqual(self.app.get('/matches').status_code, 200)
        self.assertEqual(self.app.get('/matches/1').status_code, 200)

    # Test trying to create a match on a server already in use
    def test_match_create_already_live(self):
        with self.app as c:
            with c.session_transaction() as sess:
                sess['user_id'] = 1

            # Make sure we can render the match creation page
            response = c.get('/match/create')
            self.assertEqual(response.status_code, 200)

            # Fill in its form
            response = c.post('/match/create',
                              follow_redirects=False,
                              data={
                                  'server_id': 1,
                                  'team1_id': 1,
                                  'team2_id': 2,
                                  'match_title': 'Map {MAPNUMBER} of {MAXMAPS}',
                                  'series_type': 'bo3',
                                  'veto_mappool': ['de_dust2', 'de_cache', 'de_mirage'],
                              })
            self.assertEqual(response.status_code, 200)
            self.assertIn('Error in the Server field', response.data)

    # Try starting a match using someone else's serve
    def test_match_create_not_my_server(self):
        with self.app as c:
            with c.session_transaction() as sess:
                sess['user_id'] = 2

            # Make sure we can render the match creation page
            response = c.get('/match/create')
            self.assertEqual(response.status_code, 200)

            # Fill in its form
            response = c.post('/match/create',
                              follow_redirects=False,
                              data={
                                  'server_id': 1,
                                  'team1_id': 1,
                                  'team2_id': 2,
                                  'match_title': 'Map {MAPNUMBER} of {MAXMAPS}',
                                  'series_type': 'bo3',
                                  'veto_mappool': ['de_dust2', 'de_cache', 'de_mirage'],
                              })
            self.assertEqual(response.status_code, 200)
            self.assertIn('Error in the Server field', response.data)

    # Test successful match creation
    def test_match_create(self):
        with self.app as c:
            with c.session_transaction() as sess:
                sess['user_id'] = 1

            # Make sure we can render the match creation page
            response = c.get('/match/create')
            self.assertEqual(response.status_code, 200)

            # Fill in its form
            response = c.post('/match/create',
                              follow_redirects=False,
                              data={
                                  'server_id': 2,
                                  'team1_id': 1,
                                  'team2_id': 2,
                                  'match_title': 'Map {MAPNUMBER} of {MAXMAPS}',
                                  'series_type': 'bo3',
                                  'veto_mappool': ['de_dust2', 'de_cache', 'de_mirage'],
                              })
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.location, url_for(
                'match.mymatches', _external=True))

        # Check data on the server just created
        match = Match.query.get(2)
        self.assertEqual(match.user_id, 1)
        self.assertEqual(match.team1_id, 1)
        self.assertEqual(match.team2_id, 2)
        self.assertEqual(match.max_maps, 3)
        self.assertTrue(match in User.query.get(1).matches)
        self.assertEqual(self.app.get('/match/2/config').status_code, 200)
        self.assertTrue(GameServer.query.get(2).in_use)

    def test_match_cancel(self):
        # Make sure someone else can't cancel my match when logged in
        with self.app as c:
            with c.session_transaction() as sess:
                sess['user_id'] = 2

            response = c.get('/match/1/cancel')
            self.assertEqual(response.status_code, 400)

        # Make sure someone else can't cancel my match when not logged in
        with self.app as c:
            response = c.get('/match/1/cancel')
            self.assertEqual(response.status_code, 400)

        # Cancel my match
        with self.app as c:
            with c.session_transaction() as sess:
                sess['user_id'] = 1

            response = c.get('/match/1/cancel')
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.location, url_for(
                'match.mymatches', _external=True))

        match = Match.query.get(1)
        self.assertTrue(match.cancelled)
        self.assertFalse(match.pending())
        self.assertFalse(match.live())
        self.assertFalse(match.finished())


if __name__ == '__main__':
    unittest.main()
