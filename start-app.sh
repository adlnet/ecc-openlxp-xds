#!/usr/bin/env bash
# start-server.sh

python3 manage.py waitdb 
python3 manage.py migrate --skip-checks --database default
python3 manage.py createcachetable 
python3 manage.py loaddata admin_theme_data.json 
python3 manage.py loaddata openlxp_email_templates.json 
python3 manage.py loaddata openlxp_email_subject.json 
python3 manage.py loaddata openlxp_email.json 
python3 manage.py collectstatic --no-input
cd /opt/app/ 
pwd 
./start-server.sh