get5-web BETA
===========================

This is an experimental web panel meant to be used in conjunction with the [get5](https://github.com/splewis/get5) CS:GO server plugin. It provides a more convenient way of managing matches and match servers.



Starting virtual env:
```
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

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
```
python2.7 -m unittest discover --pattern=*_test.py
```

Running web server:
```
python2.7 main.py
```

Deployment with apache2:
```
cd /var/www
git clone https://github.com/splewis/get5-web
cd get5-web
chown www-data logs
```

and inside get5.wsgi:
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
