# =============================================================================
# Get5-web
# Copyright (C) 2016. Sean Lewis.  All rights reserved.
# =============================================================================
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

#!/usr/bin/env python2.7

import get5
from get5 import db
import get5.models

import flask_script
import flask_migrate

manager = flask_script.Manager(get5.app)

# Database migrations
migrate = flask_migrate.Migrate(get5.app, get5.db)
manager.add_command('db', flask_migrate.MigrateCommand)


if __name__ == '__main__':
    manager.run()