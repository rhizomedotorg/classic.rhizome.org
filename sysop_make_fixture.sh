#!/bin/bash
source venv/bin/activate
python manage.py dumpdata --natural --indent=4 -e sessions -e admin -e contenttypes -e auth.Permission -e accounts.RhizomeUser > fixture.json
