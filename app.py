import pathlib #makes importing files easier
import requests #used for creating session objects
from pip._vendor import cachecontrol #to reduce latency
import google.auth.transport.requests #used for token request
from flask import Flask, session, abort, redirect, request, render_template
from google.oauth2 import id_token #used as id_token instance for creating an id_token and verifying the data received
from google_auth_oauthlib.flow import Flow #used for implementing the flow
import os
import mysql.connector #used in anagram program to connect flask app to mysql database
from dotenv import load_dotenv #used for loading in the .env file


load_dotenv #loads the content from the .env file (we don't want to store id or secret in public location)
app = Flask("__name__") #flask app instance
app.secret_key = os.getenv('secret_key') #using .env file to emulate a "hidden" file; purpose of secret_key is to use the session in Flask


os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1" #setting this means oauthlib will not check for secure https; if this
                                                #was for production purposes, I would configure secure https to make sure
                                                #there was secure communication


GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID') #using .env file to emulate a "hidden" file
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json") #os.path.join is used to combined multiple strings into a path
                                                                                        #pathlib.Path(__file__).parent returns current folder
                                                                                        #the contents of "client_secret.json" come from Google Cloud Console, where I created a Google App
                                                                                        #client_secret.json will be loaded and be identified as flask app client, and is better to use it rather than simply pasting the critical info into working code


flow = Flow.from_client_secrets_file(client_secrets_file=client_secrets_file,
                                     scopes=["https://www.googleapis.com/auth/userinfo.profile",
                                             "https://www.googleapis.com/auth/userinfo.email",
                                             "openid"],
                                     redirect_uri="http://127.0.0.1:5000/callback") #using OpenID Connect (OIDC) + OAuth2
                                                                                   #flow takes in 3 parameters
                                                                                   #client_secrets_file is a variable that contains a path to the json file
                                                                                   #scopes, which is permissions that the user will be asked to authorize at first
                                                                                   #openid scope value is included to indicate that OpenID Connect is being used
                                                                                   #redirect_uri is the endpoint that the Google API calls; in other words, if successfuly authenticated, then go to the redirect_uri link
                                                                                   #instead of using grant like we do in OAuth2, we use flow instead


def login_is_required(function): #creating a decorator to protect from unauthorized users; make sure its at top because they are executed in bottom-up format
    def wrapper(*args, **kwargs): #the point of having a wrapper function is that the function decorator receives function object to decorate (as input), and it must return the decorated function
        if "google_id" not in session: #to check to see if a user is logged in; flask comes with session package, and is client-side and stored in browser cookies (not encrypted);
                                       #don't want to use in production but serves its purpose here; a better solution would be to use the flask-session library, which saves sessions server-side.
                                       #It is fine to store access tokens client-side but the flask session package is not good for sensitive data because it is a cookie-based flask session
                                       #https://youtu.be/mhcnBTDLxCI
            return abort(401) #authorization required; if not authorized then http 401 unauthorized is returned
        else:
            return function() #if authorized, then return function() for wrapper function
    return wrapper #whatever is returned by the wrapper function will be returned by the login_is_required decorator

@app.route("/login") #redirect user to google consent screen using flow
def login():
    authorization_url, state = flow.authorization_url() #uses authorization function of flow, which will return an authorization url and state
    session["state"] = state #the state is a security feature, essentially a random var, that will also be sent back from authorization server
                             #here we are checking if the initial state that was created matches up with the state that was sent back by the authorization server
                             #I am storing the state in a session
    return redirect(authorization_url) #redirects user to authorization url, which is the google consent screen


@app.route("/callback") #receives data from google endpoint
def callback():
    flow.fetch_token(authorization_response=request.url) #trades what we received from google endpoint (authorization url and state) for an access token to api

    if not session["state"] == request.args["state"]: #check if state received and state in the session match
        abort(500) #if states do not match, then abort request and provide error message indicating that server was prevented from fulfilling request
                   #if states do not match, then it is likely that an outside party attempted to hack the application

    credentials = flow.credentials #credentials are being saved
    request_session = requests.Session() #creates a new requests session object
    cached_session = cachecontrol.CacheControl(request_session) #Google’s public keys are changed once per day, so we can use caching to reduce latency and reduce the potential for network errors
                                                                #We can use the CacheControl library to make our google.auth.transport.Request aware of the cache
    token_request = google.auth.transport.requests.Request(session=cached_session) #used to perform requests to Google API endpoint that requires authorization

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID) #the whole point of this is to verify the data, so we create a hook on the token request and call verify_oauth2_token method
                                   #the point of using verify_oauth2_token is to verify an ID Token issued by Google’s OAuth 2.0 authorization server
                                   #the point of using a hook is to create custom claims, thus resulting in a custom token
                                   #the token has information in it called claims, which are declarations about user & token
                                   #in this case, the claims are id_token, request, and audience
                                   #id_token is signed by the issuer with its private key, so we know origin of token
                                   #uses an extra token called id_token which proves that user is authenticated (encoded as JSON Web Token)
                                   #id_token is saved in our credentials, request is object used to make http requests, and audience is the final recipient of the token


    return redirect("/protected_resource") #redirect user to protected area

@app.route("/logout") #clear local session from user
def logout():
    session.clear() #clears session; sessions allow a user's authentication to be tracked even during several http requests
                    #in this program, cookies are used to track sessions, and user info is cleared once session.clear() is run
    return redirect("/") #redirects function to landing web page

@app.route("/") #landing page with login button
def index():
    return "Hello <a href ='/login'><button>Login</button></a>" #provides logic (using html) that makes login button redirect to /login web page

@app.route("/protected_resource") #this resource is only shown if a user is authenticated
@login_is_required #this is how you use the decorator
def protected_resource():
    return render_template("index.html") #contains desired resource (anagram project html code)


@app.route("/AddStrings", methods=["POST"]) #contains web page that will be visited after user enters two strings
def enterStrings():
    string1 = request.form["First String"].lower()
    string2 = request.form["Second String"].lower()


    db = mysql.connector.connect(user='root', password='password', #replaced original password with 'password'
                                 host='127.0.0.1',
                                 database='anagram')
    cur = db.cursor(buffered=True)

    if string1 == string2:
        cur.execute(f"""SELECT * 
                           FROM anagram.strings 
                           WHERE (string_one = '{string1}' AND string_two = '{string2}')""")
    else:
        cur.execute(f"""SELECT * 
                    FROM anagram.strings 
                    WHERE (string_one = '{string1}' OR string_two = '{string1}')
                    AND (string_one = '{string2}' OR string_two = '{string2}')""")
    row = cur.fetchone()
    if row == None:
        flag = anagramLogic(string1, string2)
        return flag
    else:
        return row[2]

def anagramLogic(string1, string2): #function for computing anagram logic (returns boolean flag) and appending to MySQL DB
    flag = False

    if sorted(string1) == sorted(string2):
        flag = True

    db = mysql.connector.connect(user='root', password='password', #replaced original password with 'password'
                                  host='127.0.0.1',
                                  database='anagram')

    cur = db.cursor(buffered=True)

    str_flag = str(flag)

    #SQL code
    cur.execute("SELECT * FROM anagram.strings")
    cur.execute(f"""INSERT INTO strings (string_one, string_two, is_anagram_flag) VALUES ('{string1}', '{string2}', '{str_flag}')""")
    db.commit()

    db.close()
    return str_flag

if __name__ == '__main__':
    app.run(debug=True)