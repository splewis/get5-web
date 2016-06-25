import unittest

from flask import url_for

import get5_test
from models import User, GameServer


class TeamTests(get5_test.Get5Test):

    # Test incorrect data server creation
    def test_server_create_invalid_data(self):
        with self.app as c:
            with c.session_transaction() as sess:
                sess['user_id'] = 1

            response = c.post('/server/create',
                              follow_redirects=False,
                              data={
                                  'ip_string': 'invalid_ip',
                                  'port': 'abcd',
                              })
            self.assertEqual(response.status_code, 200)
            self.assertIn(
                'Error in the Server IP field', response.data)
            self.assertIn(
                'Error in the Server port field', response.data)
            self.assertIn(
                'Error in the RCON password field', response.data)

    # Test successful server creation
    def test_server_create(self):
        with self.app as c:
            with c.session_transaction() as sess:
                sess['user_id'] = 1

            # Make sure we can render the team creation page
            response = c.get('/server/create')
            self.assertEqual(response.status_code, 200)

            # Fill in its form
            response = c.post('/server/create',
                              follow_redirects=False,
                              data={
                                  'ip_string': '123.123.123.123',
                                  'port': '27016',
                                  'rcon_password': 'strongpassword',
                                  'display_name': 'myserver',
                              })
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.location, url_for(
                'server.myservers', _external=True))

        # Check data on the server just created
        server = GameServer.query.get(3)
        self.assertEqual(server.user_id, 1)
        self.assertEqual(server.ip_string, '123.123.123.123')
        self.assertEqual(server.port, 27016)
        self.assertEqual(server.rcon_password, 'strongpassword')
        self.assertEqual(server.display_name, 'myserver')
        self.assertTrue(server in User.query.get(1).servers)
        self.assertFalse(server.in_use)

        # Now let's edit the server
        with self.app as c:
            with c.session_transaction() as sess:
                sess['user_id'] = 1

            response = c.post('/server/1/edit',
                              follow_redirects=False,
                              data={
                                  'ip_string': '111.123.123.123',
                                  'port': '27014',
                                  'rcon_password': 'strongpassword2'
                              })
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.location, url_for(
                'server.myservers', _external=True))

        server = GameServer.query.get(1)
        self.assertEqual(server.user_id, 1)
        self.assertEqual(server.ip_string, '111.123.123.123')
        self.assertEqual(server.port, 27014)
        self.assertEqual(server.rcon_password, 'strongpassword2')

    def test_server_deletion(self):
        # Can't delete server in use
        with self.app as c:
            with c.session_transaction() as sess:
                sess['user_id'] = 1
            response = c.get('/server/1/delete')
            self.assertEqual(response.status_code, 400)
            self.assertIn('Cannot delete when in use', response.data)

        # Can't delete some else's server when logged in
        with self.app as c:
            with c.session_transaction() as sess:
                sess['user_id'] = 2
            response = c.get('/server/2/delete')
            self.assertEqual(response.status_code, 400)
            self.assertIn('Not your server', response.data)

        # Can't delete some else's server without being logged in
        with self.app as c:
            response = c.get('/server/1/delete')
            self.assertEqual(response.status_code, 400)
            self.assertIn('Not your server', response.data)

    # Make sure a user can't edit someone else's servers
    def test_edit_server_wronguser(self):
        with self.app as c:
            with c.session_transaction() as sess:
                sess['user_id'] = 2

        response = c.post('/server/1/edit')
        self.assertEqual(response.status_code, 400)


if __name__ == '__main__':
    unittest.main()
