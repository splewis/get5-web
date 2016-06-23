get5-web BETA
===========================

[![Build Status](https://travis-ci.org/splewis/get5-web.svg?branch=master)](https://travis-ci.org/splewis/get5-web)

This is an experimental web panel meant to be used in conjunction with the [get5](https://github.com/splewis/get5) CS:GO server plugin. It provides a more convenient way of managing matches and match servers.

Note: when using this web panel, the CS:GO game servers **must** be have both the core get5 plugin and the get5_apistats plugin. They are [released](https://github.com/splewis/get5/releases) together.

**WARNING**: This should be considered BETA software - it should not be considered STABLE and will contain BUGS. Changes in the master branch may be incompatible until it is given a 1.0.0 release tag.

## Requirements:
- python2.7
- MySQL (other databases will likely work, but aren't guaranteed to)
- a web server capable of running Flask applications ([see deployment options](http://flask.pocoo.org/docs/0.11/deploying/))


## Installation
```
# Clone the repository
git clone https://github.com/splewis/get5-web
cd get5-web

# Create a virtualenv, activate it, and install dependencies
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt

# Now setup your config file
cd instance
cp prod_config.py.default prod_config.py
```
Now you can edit ``get5-web/instance/prod_config.py``, where you should change:
- ``SQLALCHEMY_DATABASE_URI``
- ``STEAM_API_KEY``
- ``SECRET_KEY``

You can also add a login whitelist if you wish (only users on the list will be able to login) and admin users:
```
WHITELISTED_IDS = [
    '76561198064755913',
]

ADMIN_IDS = [
    '76561198064755913',
]
```

Finally, initialize the database:
```
./manager.py db upgrade
```


### Deployed using Apache2 with mod_wsgi

See the [official flask documentation](http://flask.pocoo.org/docs/0.11/deploying/mod_wsgi/) for installation requirements.

This assumes you cloned the repository inside ``/var/www``.
```
cd /var/www/get5-web
chown www-data logs
```

And create ``/var/www/get5-web/get5.wsgi``, with contents:
```
#!/usr/bin/python

activate_this = '/var/www/get5-web/venv/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

import sys
import logging
logging.basicConfig(stream=sys.stderr)

folder = "/var/www/get5-web"
if not folder in sys.path:
    sys.path.insert(0, folder)
sys.path.insert(0,"")

from get5 import app as application
import get5
get5.register_blueprints()
```

Here is an example apache2 conf for /etc/apache2/sites-avaliable:
```
<VirtualHost *:80>
		ServerName get5.splewis.net
		ServerAdmin sean@splewis.net
		WSGIScriptAlias / /var/www/get5-web/get5.wsgi

		<Directory /var/www/get5>
			Order deny,allow
			Allow from all
		</Directory>

		Alias /static /var/www/get5-web/get5/static
		<Directory /var/www/get5-web/get5/static>
			Order allow,deny
			Allow from all
		</Directory>

		ErrorLog ${APACHE_LOG_DIR}/error.log
		LogLevel warn
		CustomLog ${APACHE_LOG_DIR}/access.log combined
</VirtualHost>
```


## Other useful commands:

Autoformatting:
```
cd get5
autopep8 -r get5 --in-place
autopep8 -r get5 --diff # should have no output
```

Linting errors:
```
cd get5
pyflakes *.py
```

Testing:
You must also setup a ``test_config.py`` file in the ``instance`` directory.
```
./test.sh
```

Manually running a test instance: (for development purposes)
```
python2.7 main.py
```
