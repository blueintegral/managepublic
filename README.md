# manage.engineer
Manage engineers and schedules with Smartsheet and other integrations.

Authored by Hunter. This is alpha software. Contributions much appreciated!

## Running it
After installing dependancies, run:

```export FLASK_APP=app.py```

```export FLASK_ENV=development```

```flask run```

## Tour
/smartsheet_archive -> Downloaded json files of every Smartsheet project on the specified date. Naming convention is yyyy-mm-dd-smartsheet_id.json. Smartsheet IDs can be found in File->Properties of the Smartsheet you want on the Smartsheet website.

/static -> Contains all static HTML assets 

/templates -> Contains all HTML Jinja templates for Flask

app.py -> Main file that Flask runs. Contains render functions and handles GETs and POSTs.

client_secret.json -> Private key for Smartsheet API. 

manage.py -> Where the real work happens.

people_cache -> Pickle file to write the generated HTML for the /people page, since generating takes a long time. This is my jank version of a cache. Is overwritten when the user requests a complete refresh.

schedule_cache -> Same thing as the people_cache, but for the /schedule page.

token.pkl -> Pickle file of private key for Google Calendar API
