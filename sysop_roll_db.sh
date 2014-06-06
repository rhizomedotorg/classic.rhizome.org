#!/bin/bash

# destroy db
python manage.py flush

# resync
python manage.py syncdb

# load fixtures
python manage.py loaddata fixture.json
cat fixture.sql | python manage.py dbshell
