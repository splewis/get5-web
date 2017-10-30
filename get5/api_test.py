import unittest

import get5_test
from models import Match, MapStats, PlayerStats, GameServer


class ApiTests(get5_test.Get5Test):

    # Full test of the match stats api.

    def test_match_stats(self):
        # Make sure the match page can be rendered
        self.assertEqual(self.app.get('/match/1').status_code, 200)
        self.assertEqual(self.app.get('/matches').status_code, 200)
        self.assertEqual(self.app.get('/matches/1').status_code, 200)

        match = Match.query.get(1)
        matchkey = match.api_key
        self.assertTrue(match.pending())
        self.assertFalse(match.live())
        self.assertFalse(match.finished())
        self.assertFalse(match.cancelled)

        # Make sure no map stat object exists already
        mapstat = MapStats.query.filter_by(
            match_id=match.id, map_number=0).first()
        self.assertTrue(mapstat is None)

        # Start the first map
        response = self.app.post('/match/1/map/0/start',
                                 data={
                                     'mapname': 'de_dust2',
                                     'key': matchkey,
                                 })
        self.assertEqual(response.status_code, 200)

        match = Match.query.get(1)
        self.assertEqual(match.id, 1)
        self.assertFalse(match.pending())
        self.assertTrue(match.live())
        self.assertFalse(match.finished())

        mapstat = MapStats.query.filter_by(match_id=1, map_number=0).first()
        self.assertEqual(mapstat.match_id, 1)
        self.assertEqual(mapstat.map_number, 0)
        self.assertEqual(mapstat.map_name, 'de_dust2')
        self.assertTrue(mapstat.start_time is not None)
        self.assertTrue(mapstat.end_time is None)
        self.assertEqual(mapstat.team1_score, 0)
        self.assertEqual(mapstat.team2_score, 0)

        # Send a score update
        response = self.app.post('/match/1/map/0/update',
                                 data={
                                     'team1score': '6',
                                     'team2score': '7',
                                     'key': matchkey,
                                 })
        self.assertEqual(response.status_code, 200)
        mapstat = MapStats.query.filter_by(match_id=1, map_number=0).first()
        self.assertEqual(mapstat.team1_score, 6)
        self.assertEqual(mapstat.team2_score, 7)

        # Send a player stats update
        response = self.app.post(
            '/match/1/map/0/player/76561198053858673/update',
                                 data={
                                     'roundsplayed': '5',
                                     'kills': '5',
                                     'deaths': '3',
                                     'damage': '500',
                                     'team': 'team1',
                                     'key': matchkey,
                                 })
        self.assertEqual(response.status_code, 200)
        playerstats = PlayerStats.query.filter_by(
            match_id=1, map_id=1, steam_id=76561198053858673).first()
        self.assertEqual(playerstats.kills, 5)
        self.assertEqual(playerstats.team_id, 1)

        # Send map finish
        response = self.app.post('/match/1/map/0/finish',
                                 data={
                                     'winner': 'team1',
                                     'key': matchkey,
                                 })
        self.assertEqual(response.status_code, 200)
        mapstat = MapStats.query.filter_by(match_id=1, map_number=0).first()
        self.assertEqual(mapstat.winner, 1)

        # Send series finish
        response = self.app.post('/match/1/finish',
                                 data={
                                     'winner': 'team1',
                                     'key': matchkey,
                                 })
        self.assertEqual(response.status_code, 200)
        match = Match.query.get(1)
        self.assertEqual(match.winner, 1)
        self.assertFalse(match.pending())
        self.assertFalse(match.live())
        self.assertTrue(match.finished())
        self.assertFalse(GameServer.query.get(1).in_use)

        # Try to send series finish again, should fail
        response = self.app.post('/match/1/finish',
                                 data={
                                     'winner': 'team1',
                                     'key': matchkey,
                                 })
        self.assertEqual(response.status_code, 400)
        self.assertIn('Match already finalized', response.data)

        # Should still be able to render match pages
        self.assertEqual(self.app.get('/match/1').status_code, 200)
        self.assertEqual(self.app.get('/matches').status_code, 200)
        self.assertEqual(self.app.get('/matches/1').status_code, 200)

    def test_match_stats_wrong_api_key(self):
        self.assertEqual(self.app.get('/match/1').status_code, 200)
        self.assertEqual(self.app.get('/matches').status_code, 200)
        self.assertEqual(self.app.get('/matches/1').status_code, 200)
        data = {
            'key': 'abc',
        }

        response = self.app.post('/match/1/map/0/start', data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Wrong API key', response.data)

        response = self.app.post('/match/1/map/0/update', data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Wrong API key', response.data)

        response = self.app.post('/match/1/map/0/finish', data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Wrong API key', response.data)

        response = self.app.post('/match/1/finish', data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Wrong API key', response.data)

    def test_rate_limiting(self):
        match = Match.query.get(1)
        data = {
            'key': match.api_key,
        }

        # first response should be work
        response = self.app.post('/match/1/map/0/start', data=data)
        self.assertEqual(response.status_code, 200)

        # send 100 more requests
        for i in range(1, 100):
            response = self.app.post('/match/1/map/0/start', data=data)

        self.assertEqual(response.status_code, 429)  # too many requests

    def test_rate_limiting_different_keys(self):
        match = Match.query.get(1)
        data = {
            'key': match.api_key,
        }

        # first response should be work
        response = self.app.post('/match/1/map/0/start', data=data)
        self.assertEqual(response.status_code, 200)

        # send 500 more requests
        for i in range(1, 500):
            data = {
                'key': str(i),
            }
            response = self.app.post('/match/1/map/0/start', data=data)

        self.assertEqual(response.status_code, 429)  # too many requests


if __name__ == '__main__':
    unittest.main()
