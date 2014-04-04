# Rhizome.org

Online since 1996.    
Open source since 2014.

**rationale**

This document provides instructions for installing and running rhizome.org locally for development. Caveats: ArtBase, search and payment processing don't work locally. Powered by [Django](https://www.djangoproject.com/).

## Install

```
$ git clone git@github.com:rhizomedotorg/rhizome.org.git
```

**configure**

```
$ cd path/to/rhizome.org/
$ cp rhizome/local_settings_example.py rhizome/local_settings.py
```

open `local_settings.py` and set `SECRET_KEY` to some string, ([docs](https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-SECRET_KEY)), may also want to change `DATABASES` configuration.

### setup env

Install virtualenv ([docs](http://www.virtualenv.org/en/latest/virtualenv.html#installation))

```
virtualenv venv
source venv/bin/activate
```

**install dependencies**

hold your breath!

```
pip install -r requirements.txt
```

### load fixtures

```
sh sysop_roll_db.sh
```

ignore these errors:

`Could not access or create artbase CouchDB database`    
`Failed to install index for...`

## Usage

```
$ cd /path/to/rhizome.org
$ source venv/bin/activate
$ python manage.py runserver
```

navigate to [http://localhost:8000](localhost:8000)

**admin panel**

[http://localhost:8000/rza/](localhost:8000/rza/)    
username: staffuser    
password: 123

## Documentation

(coming soon)

got a question? open an issue.    
for support contact scott.meisburger@rhizome.org.
