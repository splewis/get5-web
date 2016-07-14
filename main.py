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

import argparse
import sys

import get5

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Testing web server for get5.')
    parser.add_argument('--host', default='127.0.0.1',
                        help='ip for the server to listen on')
    parser.add_argument('--port', '-p', type=int, default=5000,
                        help='port for the server to listen on')
    args = parser.parse_args()

    get5.register_blueprints()
    sys.stderr.write(' * Starting get5 testing server. This is for testing only, do not run in production\n')
    get5.app.run(host=args.host, port=args.port)
