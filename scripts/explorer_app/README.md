To run it go to your virtualenv and install flask:

`pyinstall flask`

and run it with:

either:

`python app.py`

or to be fancier (this runs it in a monitoring mode so the server just restarts automatically with code changes):

`FLASK_APP=/users/is/skhare/git/shashank_scripts/explorer_app/app.py FLASK_ENV=development flask run --host 0.0.0.0 --port 5388`


Notes:

The default hardcoded env is mktdatad, change it to research for research libs.