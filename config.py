# Example Config File

import pyrebase

Event = ""
Schedlink = ""
Trackerlink = ""
Root_Dir = ""
OAuthToken = ""
urlregexmatch = ""

firebasecfg = {
	"apiKey": "apiKey",
	"authDomain": "authDomain",
	"databaseURL": "databaseURL",
	"projectId": "projectID",
	"serviceAccount": "serviceAccountJSONFile"
}

firebase = pyrebase.initialize_app(firebasecfg)
auth = firebase.auth()
user = auth.sign_in_with_email_and_password("emailaddress","password")
db = firebase.database()

def refresh():
	global user
	user = auth.refresh(user['refreshToken'])
	return
	
