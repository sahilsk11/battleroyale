#!/usr/bin/python

print "Content-type: text/html\n\n\r"

import shelve
import json
import cgi
import random
import datetime
import requests

form = cgi.FieldStorage()
username = form.getfirst("username", "")
platform = form.getfirst("platform", "")

client_id = form.getfirst("client_id", "")
redirect_uri = form.getfirst("redirect_uri", "")
response_type = form.getfirst("response_type", "")
state = form.getfirst("state", "")

#called from Alexa
if ((platform == "" or username == "") and (state != "" and redirect_uri != "")):
    f = open("index.html")
    html_text = f.read()
    html_text = html_text.replace("p1", "\""+redirect_uri+"\"")
    html_text = html_text.replace("p2", "\""+state+"\"")
    print html_text
elif (platform != "" and username != ""):
    headers = {"TRN-Api-Key":"07e80b10-398c-4d66-9078-00fcae0d6b25"}
    url = "https://api.fortnitetracker.com/v1/profile/%s/%s" % (platform, username)
    html_response = requests.get(url, headers=headers)
    if (html_response.status_code == 200):
        response = html_response.json()
        if (response.has_key("error")):
            f = open("user.html")
            print f.read()
        else:
            token = platform+username
            print "<script>window.location=\""+redirect_uri+"?code="+token+"&state="+state+"\"</script>"
    else:
        print("Could not access database")
else:
    f = open("notfound.html")
    print f.read()
    
    


