# OAuth2-Google-Login
Overview:

In this project, my goal was to secure my web application's api calls by using OAuth 2.0, a protocol designed to add authorization to an API. However, instead of simply implementing OAuth 2.0 to secure a REST api, I decided to integrate OpenID Connect (OIDC) and Python's Google OAuth Library to create a Google Login using Authorization Code Flow for my application. This is similar to a mobile app requesting a user for permission to use certain information pertaining to the user, but rather I was building the process behind this entire operation.


The process is as follows (skip to TLDR section if you want to read shorter explanation):

OAuth 2.0 Authorization Code Flow + OIDC:
- Registering Web Application with OAuth 2.0 provider (Google in my case):
	- Before entering the flow, I first registered my application in the Google Developer Console to use the Authorization Code Flow + OIDC.
	- Provide Google Developer Console with name of application, where the application is hosted, and a redirect/callback uri
	- Once registered, we receive:
		- Client ID : to identify the client as an application 
		- Client Secret: to authenticate the client when a request for an access token is made
		- Authorization Server URL: a URL for the client to request authorization
		- Access Token URL: a URL for the client to exchange an authorization code for an access token
		- Certs URL: provides public certificates for verifying ID tokens issued by Google OAuth 2.0's authorization server
		- Resource Server URL: could be same as authorization server url in some cases
	- Added all this information to my program by downloading the json file

- Authorization Request:
	- Web application requests permission from the user to authorize access to their account hosted at a third-party OAuth2 provider
	- Flow created on line 30, which includes json file, scopes that represent what you want to access (profile, email, and openid --> to use OIDC to obtain id token), and redirect uri for where to go after authorization
	- From the flow created, the web application can obtain the authorization url and state (line 56)
		- this is done in the login function
		- authorization url consists of:
			- Response type: tells authorization server which grant or flow to use: code in my case
			- Client ID: identifies web application
			- Redirect URI: where to redirect user to
			- Scope: specifies which portions of the user profile the web application wishes to access
			- State: is a randomly-generated string that the web application provides, which the authorization server will simply pass back so that the web application can then validate to mitigate fraud
		- state is stored in session on line 57
			- after user authorizes, we will be sent back to client in order to send the authorization code; there we will compare the state received with authorization code to the state that exists within the session (line 66)
		- So going back to where we were, the user is then redirected to authorization url on line 59
		- Google's Authorization server will present them with a prompt asking if they would like to authorize this application’s request

- Authorization Grant + Authorization Code (api to client):
	- After the user authorizes the web application to access their third-party account, the authorization server will redirect the user back to the web application via the redirect URL (which I included in Google Developer Console and is a part of authorization url --> https://127.0.0.1:5000/callback) with the following information:
		- Code: a short-lived authorization code that the web application expects from authentication server
		- State: the state credential passed earlier from the web application
	- Basically means url = redirect url + code + state --> all combined into one url
	- This is done for us automatically when the user authorizes the web application (basically what occurs after line 59 is run)

- Fetch Token (client to api):
	- Now we are going to access the callback function on line 63 (after user is authorized)
	- We are exchanging the authorization code for the access token on line 64
		- line 64 uses the redirect url + code + state to fetch the token because it includes the authorization code needed to trade for the access token
		- The web application sends an HTTP POST request to the authorization server's token endpoint with the following (line 64 + line 75):
			- Grant Type: tells the authorization server, again, which flow or grant to use --> code
			- Code: the authorization code received from the authorization server
			- Redirect URI: where to redirect the user back to
			- Client ID: the same client identifier used in the authorization step
			- Client Secret: the password equivalent provided by the OAuth2 provider during registration
	- Fetch token sets up the trade for authorization code and access token, while token request performs the request to token endpoint
	- As mentioned earlier, we also check if the state received from the google endpoint matches the state in the session we set earlier on line 66
		- This prevents any malicious attempts
	- state is likely stored in cache 

- Receive Access Token (api's authorization server to client):
	- The token endpoint on the authorization server will verify all the parameters in the request
		- Ensures authorization code hasn't expired
		- This is where we check that the client id and client secret in the authorization code match the client id and client secret created in the Google Developer Console
	- If successful, then the access token is sent to the client --> this process occurs on line 75

	- Tried to challenge myself so I implemented OIDC, id token, took advantage of inline hook (triggered when OAuth 2.0 + OIDC tokens are minted)
	- Received ID token along with access token (and used hook to verify id token)
		- hook is automatically created when token request on line 75 is called
		- hooks are generally used for custom claims, but in this case I am using it to call verify_oauth2_token function in order to verify that token is valid and that certain claims in the jwt id token match the parameters that they are supposed to be (all on lines 75-80)
		- The token_request also results in the authorization server sending an id token
		- Stored credentials in variable on line 71 for setting id_token credentials in id_info parameter on line 78
		- request is still token_request because we set one of the scopes equal to "openid" when creating the flow on line 30
		- audience is equal to the GOOGLE_CLIENT_ID on line 80 because the web application is what will use the information received within the id token
		- Although my flask application that I built does not make use of the the profile / email, I could implement this by creating an application that stores user information by creating accounts with their profile and email

- Don't Need To Use Access Token (client to api's resource server):
	- Typically, the web application sends an HTTP GET request to the resource server in order to use the access token to obtain the protected resources; resource server will validate access token and if valid will send protected resources back
	- However in my case, this is not necessary as I am not accessing any information stored on another API, but rather granting a user access to add to a mysql database. 
	- All I need to do is:
		- Before accessing the protected resource, on line 89 we make sure to set the session["google_id"] equal to the "sub" key found in the id token so that when when we access the protected resource, the decorator function's if condition is passed (on line 45). The point of this is to ensure that the session would only contain "google_id" if we are in the correct session. Therefore, we have access to the protected resource.






TLDR explanation:

- Application sends authorization and authentication request to authorization endpoint
- User is redirected to Google Login page and user receives permissions request 
- Once permissions are granted and user is authorized, the authorization server sends an authorization code to the application
- The application then "trades" the authorization code in exchange for an access token and id token from the authorization server. This is done by the application using a token request to the token endpoint, whereby the token endpoint promptly sends back the access token and id token
- The id token (from OIDC) caches user profile info and provides it to the client. The client consumes this id token and obtains user info from it in order to personalize user experience; id tokens follow the JSON web tokens (JWT) format, which is why I use claims in my code about the id token itself
	- The claims about the authenticated user are usually pre-defined by OIDC, but in my case I created custom claims
- The access token (from OAuth 2.0) is used to retrieve the relevant information (resource) determined by the scopes from the resource server (Google API Server), which was the initial goal set out by the user


Diagram Explaining What Is Occurring:

![image](https://user-images.githubusercontent.com/81287555/190895807-d30f4f1b-345b-422a-9f81-80b61302911f.png)
![image](https://user-images.githubusercontent.com/81287555/190895820-6b9fe376-c673-4f36-bacb-cd4d31721ce5.png)



I used OIDC for user authentication and OAuth 2.0 for resource access/sharing and authorizing third-party login. It should be noted that OpenID Connect is an identity layer on top of the OAuth 2.0 protocol.


	- Steps to accomplish this:
		- Set Up:
			- Created new project under Google Developer Console
			- Created new credentials and selected OAuth Client ID 
			- Set application type as web application, and authorized a redirect uri
			- Once this was done, I received a Client ID and a Client Secret
			- I then downloaded the JSON file containing client info, urls, and the redirect_url to include in my application
			- To get all of the appropriate modules, I used the 'pip > freeze requirements.txt' command in order to write them to the requirements.txt file
			- I also included the dotenv library to emulate using a file hidden from view
		- Writing the application:
			- High-Level description of my code:
				- Created a path to my JSON file that I downloaded from OAuth 2.0 Client IDs
				- Created a flow based on the JSON file using Google's OAuth Library
				- Wrote a decorator, which included a wrapper function in order to ensure that only authorized users can access the protected resource
				- Then I created five new endpoints for different purposes
					- logging in (authorization url and state, redirects to Google Consent Screen)
					- logging out (clears session)
					- landing page (login button)
					- callback (trades for access token, checks if states match, id token, cache control, redirects to protected resource)
					- protected resource (my previous Flask application code)
				- I also added my previous Flask project's code to the protected resource endpoint as well as several functions to the application
			- A much more thorough understanding of what is going on exists in the the detailed comments in the application code
