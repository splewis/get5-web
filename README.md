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
cd get5
python2.7 -m unittest discover --pattern=*_test.py
```

Running web server:
```
python2.7 main.py
```
