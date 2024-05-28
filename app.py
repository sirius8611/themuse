from flask import Flask, redirect, render_template, url_for, session, request, jsonify
from flask_session import Session
import os
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
from flask import render_template

# Flask app setup
app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# OAuth 2.0 Client ID JSON file path
CLIENT_SECRETS_FILE = "client_secret2.json"

# Scopes for accessing Google Calendar
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
API_SERVICE_NAME = 'calendar'
API_VERSION = 'v3'  

@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/profile')
def profile():
    if 'credentials' not in session:
        return redirect('signin')
    
    # Load credentials from the session
    credentials = google.oauth2.credentials.Credentials(
        **session['credentials'])

    # Use the credentials to create a Google Calendar API client
    service = googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials)

    # Fetch calendar events
    events_result = service.events().list(calendarId='primary', maxResults=10, singleEvents=True, orderBy='startTime').execute()
    events = events_result.get('items', [])

    return render_template('profile.html', events=events)

@app.route('/signin')
def signin():
    # Create the flow using the client secrets file
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES)

    flow.redirect_uri = url_for('home', _external=True)

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true')

    # Store the state in the session to verify the response later
    session['state'] = state

    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    # Specify the state when creating the flow in the callback to prevent cross-site request forgery
    state = session['state']

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = url_for('oauth2callback', _external=True)

    # Use the authorization server's response to fetch the OAuth 2.0 tokens
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    # Store credentials in the session
    credentials = flow.credentials
    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

    return redirect(url_for('profile'))

@app.route('/signout')
def signout():
    # Clear the credentials from the session
    if 'credentials' in session:
        del session['credentials']
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
