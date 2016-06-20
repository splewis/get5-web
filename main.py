#!/usr/bin/env python2.7

import get5


if __name__ == '__main__':
    get5.db.create_all()
    get5.register_blueprints()
    get5.app.run()
