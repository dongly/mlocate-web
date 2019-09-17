from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import flask
from subprocess import Popen, PIPE
from flask import send_from_directory
from socket import gethostname
from pipes import quote
import glob, os, hashlib

MAX_RESULT_BYTES = os.getenv('MAX_RESULT_BYTES', 1000000)  # set to -1 to disable limit
MAX_DATABASES = os.getenv('MAX_DATABASES', 5)
PAGE_TITLE = os.getenv('PAGE_TITLE', 'mlocate web search')
PAGE_HEADING = os.getenv('PAGE_HEADING', 'Simple mlocate search')
HOSTNAME = os.getenv('HOSTNAME', gethostname() )
APP_ROUTE = os.getenv('APP_ROUTE', '/')
if not APP_ROUTE.startswith('/'):
    APP_ROUTE = '/' + APP_ROUTE
if not APP_ROUTE.endswith('/'):
    APP_ROUTE = APP_ROUTE + '/'

app = flask.Flask(__name__)

databases = glob.glob('/app/databases/*.db')
databases = databases[:MAX_DATABASES]

databaselist = {}
for database in databases:
    name = os.path.basename(database)
    databaselist[name] = {}
    databaselist[name]['label'] = os.path.basename(database)[:-3].title()
    databaselist[name]['checked'] = 'checked'

def getitem(obj, item, default):
    if item not in obj:
        return default
    else:
        return obj[item]

@app.route(APP_ROUTE)
def main():
  return flask.redirect(APP_ROUTE + 'index')

@app.route(APP_ROUTE + 'index')
def index():
    # handle user args
    args = flask.request.args
    query = getitem(args, 'searchbox', '')
    if getitem(args, 'caseSensitive', '') == 'on':
        cs = 'checked'
    else:
        cs = 'unchecked'
    dbsearch = ''
    for database in databaselist.keys():
        if getitem(args, database, '') == 'on':
            databaselist[database]['checked'] = 'checked'
            dbsearch = dbsearch + ' -d ' + quote('/app/databases/' + database)
        else:
            databaselist[database]['checked'] = 'unchecked'
    if query == '':
        resultslist = '<div class="alert alert-info" role="alert">Please Enter a search Query</div>'
        results_truncated = False
    else:
        if cs != 'checked':
            cs = ' -i '
        else:
            cs = ''
        command = 'mlocate ' + dbsearch + cs + quote(query)
        command = command.encode('utf-8')
        with Popen(command, shell=True, stdout=PIPE) as proc:
            outs = proc.stdout.read(MAX_RESULT_BYTES)
        results = outs.splitlines()
        results_truncated = len(outs) == MAX_RESULT_BYTES
        if results_truncated:
            results = results[:-1]
        resultslist = ''
        for entry in results:
            thisresult = os.path.basename(entry).decode('utf-8')
            thishash = hashlib.md5(thisresult.encode('utf-8')).hexdigest()
            thispath = '&#92;' + entry.decode('utf-8').replace('/', '&#92;')
            resultslist = resultslist + '<label class="file-label" for="' + thishash + '">' + thisresult + '</label><textarea readonly id="' + thishash + '" type="text" value="' + thispath + '" class="allowCopy noselect">' + thispath + '</textarea>'

    html = flask.render_template(
        'index.html',
        searchbox=query,
        cs=cs,
        databaselist=databaselist,
        results_truncated=results_truncated,
        resultslist=resultslist,
        pagetitle=PAGE_TITLE,
        pageheading=PAGE_HEADING,
        hostname=HOSTNAME)
    return html

@app.route(APP_ROUTE + 'css/<path:path>')
def send_css(path):
    return send_from_directory('css', path)

@app.route(APP_ROUTE + 'js/<path:path>')
def send_js(path):
    return send_from_directory('js', path)

if __name__ == '__main__':
    port = 5000
    app.run(debug=False,host='0.0.0.0',port=port)
