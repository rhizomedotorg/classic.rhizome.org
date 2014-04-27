# Rhizome.org

Online since 1996.    
Free and open-source software (FOSS) since 2014.

**rationale**

This document provides instructions for installing and running rhizome.org locally for development. Caveats: ArtBase, search and payment processing don't work locally. Powered by [Django](https://www.djangoproject.com/).

## Install

```
$ git clone https://github.com/rhizomedotorg/rhizome.org.git
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

*for PIL to compile correctly on OS X, might have to do this first:*

```
export CFLAGS=-Qunused-arguments
export CPPFLAGS=-Qunused-arguments
```

### load fixtures

```
sh sysop_roll_db.sh
```

## Usage

```
$ cd /path/to/rhizome.org
$ source venv/bin/activate
$ python manage.py runserver
```

navigate to [http://localhost:8000](localhost:8000)

ignore these errors (at any point you see them):

`Could not access or create artbase CouchDB database`
`Failed to install index for...`

**admin panel**

[http://localhost:8000/rza/](localhost:8000/rza/)    
username: staffuser    
password: 123

## Documentation

(coming soon)

got a question? open an issue.    
for support contact scott.meisburger@rhizome.org.
