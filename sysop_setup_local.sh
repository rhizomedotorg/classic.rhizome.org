#!/bin/bash

# install dependencies
pip install -r requirements.txt

# destroy db
python manage.py sqlflush | sed 's/TRUNCATE/DROP TABLE/g'| python manage.py dbshell

# resync
python manage.py syncdb

# load fixtures
python manage.py loaddata fixture.json
cat fixture.sql | python manage.py dbshell
