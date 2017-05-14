import unittest
import logging

import get5
from get5 import db
from models import User, Team, GameServer, Match


# All tests will use this base test framework, including the test date defined
# in create_test_data. This data will already be in the database on test start.
class Get5Test(unittest.TestCase):

    def setUp(self):
        get5.app.config.from_pyfile('test_config.py')
        get5.app.logger.setLevel(logging.ERROR)
        self.app = get5.app.test_client()
        get5.register_blueprints()
        db.create_all()
        self.create_test_data()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def create_test_data(self):
        user = User.get_or_create(123)
        user.admin = True
        User.get_or_create(12345)
        db.session.commit()

        team1 = Team.create(user, 'EnvyUs', 'EnvyUs', 'fr',
                            'nv', ['76561198053858673'])
        team2 = Team.create(user, 'Fnatic', 'Fnatic', 'se', 'fntc',
                            ['76561198053858673'])
        server = GameServer.create(
            user, 'myserver1', '127.0.0.1', '27015', 'password', False)
        server.in_use = True

        GameServer.create(user, 'myserver2', '127.0.0.1', '27016', 'password', True)
        db.session.commit()

        Match.create(user, team1.id, team2.id, '', '', 1, False,
                     'Map {MAPNUMBER}', ['de_dust2', 'de_cache', 'de_mirage'], server.id)
        db.session.commit()
