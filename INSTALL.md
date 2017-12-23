<p align="center">
<img src="http://i.imgur.com/iqvMAWb.png">
</p>

<h1 align="center">Ubuntu 16.04+</h1>

## 1: Ubuntu

If you are new to using Ubuntu, there is a guide on [Digital Ocean's community tutorial site](https://www.digitalocean.com/community/tutorials/initial-server-setup-with-ubuntu-14-04) that will provide information on how to setup and configure the operating system.

## 2: Dependencies

> You will be required to setup a DNS record from a sub domain in order to use get5-web. For more information on how to do that, view [here](https://www.namecheap.com/support/knowledgebase/article.aspx/319/2237/how-can-i-set-up-an-a-address-record-for-my-domain)

> Get5-Web requires **other software** installed on your Ubuntu machine. Run these commands in your terminal window.

```sh
sudo apt-get update && apt-get upgrade -y
sudo apt-get install build-essential software-properties-common -y
sudo apt-get install python-dev python-pip apache2 libapache2-mod-wsgi -y
sudo apt-get install virtualenv libmysqlclient-dev -y
```

> Installing  MySQL

```sh
sudo apt-get install mysql-server
```

You will be presented with a menu to select a root password, please use a secure password here and remember this password. You will need it later.

## 3: Creating the MySQL Database

> In order to use get5 correctly, we will need to setup a database if you have not already done so.

```sh
mysql -u root -p
```

> You will be prompted to enter a password, enter the password you used when you installed MySQL. Once logged in, follow the next step, replacing `password` with a password for the new user.

```sql
GRANT ALL PRIVILEGES ON get5.* TO 'get5'@'localhost' IDENTIFIED BY 'password';
FLUSH PRIVILEGES;
CREATE DATABASE get5;
quit
```

## 4: Clone

Run the following commands to download Get5-Web. This will place it in a **new folder** called `get5-web`, which we will immediately enter.

```sh
cd /var/www
git clone https://github.com/splewis/get5-web
cd get5-web
```

## 5: Creating the Virtual Environment

> We must now configure the python environment for which the process will run.

```sh
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 6: Configuration

> We will now setup the config for your application.

```sh
cd instance
cp prod_config.py.default prod_config.py
```

> Next, open up `prod_config.py` and change the values as follows:

- `SQLALCHEMY_DATABASE_URI`: `'mysql://get5:<password>@localhost/get5'`
- `STEAM_API_KEY `: `<YOUR API KEY>`
  - Retrievable from https://steamcommunity.com/dev/apikey
- `SECRET_KEY`:
  - Random key. Generate some random text into here.

> With the core configuration completed, there are now more advanced options available. These are documented inside the configuration file. Should you wish to whitelist the panel to specific users, look into the `WHITELISTED_IDS` and `ADMIN_IDS` section.

## 7: Database Migrations

> With the configuration now completed, we can now import the tables into the database.

```sh
cd ../
./manager.py db upgrade
```

## 8: Logo Support

> If you want logos to be available to use from your panel, these should be uploaded into `get5/static/img/logos`. A good source is http://csgo-data.com/.

## 9: WSGI Configuration

> To ensure that logging can occur properly, we need to set correct permissions for the web user.

```sh
cd /var/www/get5-web
chown -R www-data logs
```

> Next, we need to create a WSGI file, which will send our python application to the webserver. Create `/var/www/get5-web/get5.wsgi`, and insert the following code block into the file before saving.

```python
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

## 10: Webserver Configuration

> We now need to setup Apache to process the content, do this by creating `/etc/apache2/sites-enabled/get5.conf`, with the following content. Be sure to change `<hostname>` to be your chosen sub domain, and `<email>` with your email if required. **A SERVER IP WILL NOT WORK**.

```apache
<VirtualHost *:80>
	ServerName <hostname>
	ServerAdmin <email>
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

> After this, we just need to restart the webserver

```sh
service apache2 restart
```

## 11: Finished

> Navigate to your sub domain in the browser and view the finished results.
