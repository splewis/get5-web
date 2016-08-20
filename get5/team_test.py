import unittest

from flask import url_for

import get5_test
from models import User, Team


class TeamTests(get5_test.Get5Test):

    def test_render_pages(self):
        self.assertEqual(self.app.get('/teams/1').status_code, 200)
        self.assertEqual(self.app.get('/team/1').status_code, 200)
        self.assertEqual(self.app.get('/team/1').status_code, 200)

    def test_team_create_not_logged_in(self):
        # This should redirect to the login page
        with self.app as c:
            response = c.get('/team/create')
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.location,
                             url_for('login', _external=True))

    def test_team_create(self):
        with self.app as c:
            with c.session_transaction() as sess:
                sess['user_id'] = 1

            # Make sure we can render the team creation page
            response = c.get('/team/create')
            self.assertEqual(response.status_code, 200)

            # Fill in its form
            response = c.post('/team/create',
                              follow_redirects=False,
                              data={
                                  'name': 'NiP',
                                  'country_flag': 'se',
                                  'logo': 'nip',
                                  'auth1': 'STEAM_0:1:52245092',
                              })
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.location, url_for(
                'team.teams_user', userid=1, _external=True))

        # Make sure the team was actually created
        team = Team.query.filter_by(name='NiP').first()
        self.assertEqual(team.id, 3)  # already 2 test data teams
        self.assertEqual(team.user_id, 1)
        self.assertEqual(team.name, 'NiP')
        self.assertEqual(team.flag, 'se')
        self.assertEqual(team.logo, 'nip')
        self.assertEqual(team.auths[0], '76561198064755913')
        self.assertTrue(team in User.query.get(1).teams)

        # Should be able to render the teams page
        self.assertEqual(self.app.get('/teams/1').status_code, 200)

        # Edit the team
        with self.app as c:
            with c.session_transaction() as sess:
                sess['user_id'] = 1

            # Make sure we can render the team edit page
            response = c.get('/team/3/edit')
            self.assertEqual(response.status_code, 200)

            # Fill in its data
            response = c.post('/team/3/edit',
                              follow_redirects=False,
                              data={
                                  'name': 'NiP2',
                                  'country_flag': 'ru',
                                  'logo': 'newlogo',
                                  'auth1': 'STEAM_0:1:52245092',
                              })
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.location, url_for(
                'team.teams_user', userid=1, _external=True))

        team = Team.query.get(3)
        self.assertEqual(team.name, 'NiP2')
        self.assertEqual(team.flag, 'ru')
        self.assertEqual(team.logo, 'newlogo')

        # Now delete the team
        with self.app as c:
            with c.session_transaction() as sess:
                sess['user_id'] = 1

            response = c.get('/team/3/delete')
            self.assertEqual(response.status_code, 302)
        team = Team.query.get(3)
        self.assertIsNone(team)

    # Make sure a user can't edit someone else's teams
    def test_edit_team_wronguser(self):
        with self.app as c:
            with c.session_transaction() as sess:
                sess['user_id'] = 2

            response = c.post('/team/1/edit')
            self.assertEqual(response.status_code, 400)

    # Make sure a non-logged in user can't edit someone else's teams
    def test_edit_team_nouser(self):
        with self.app as c:
            response = c.post('/team/1/edit')
            self.assertEqual(response.status_code, 400)

    # Make sure a user can't delete someone else's teams
    def test_delete_team_wronguser(self):
        with self.app as c:
            with c.session_transaction() as sess:
                sess['user_id'] = 2

            response = c.get('/team/1/delete')
            self.assertEqual(response.status_code, 400)

    def test_myteams_redirect(self):
        with self.app as c:
            with c.session_transaction() as sess:
                sess['user_id'] = 1

            # Make sure we can render the team creation page
            response = c.get('/myteams')
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.location, url_for(
                'team.teams_user', userid=1, _external=True))

    # TODO:
    # - test public team creation, editing, redirects


if __name__ == '__main__':
    unittest.main()
