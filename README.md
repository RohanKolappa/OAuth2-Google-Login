# OAuth2-Google-Login
Overview:

In this project, my goal was to secure my web application's api calls by using OAuth 2.0, a protocol designed to add authorization to an API. However, instead of simply implementing OAuth 2.0 to secure a REST api, I decided to integrate OpenID Connect (OIDC) and Python's Google OAuth Library to create a Google Login using Authorization Code Flow for my application. This is similar to a mobile app requesting a user for permission to use certain information pertaining to the user, but rather I was building the process behind this entire operation.


The process is as follows:
- Application sends authorization and authentication request to authorization endpoint
- User is redirected to Google Login page and user receives permissions request 
- Once permissions are granted and user is authorized, the authorization server sends an authorization code to the application
- The application then trades the authorization code for an access token from the authorization server using a token request to the token endpoint
- The 

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
