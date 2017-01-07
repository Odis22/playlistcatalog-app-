from flask import Flask, render_template, request, redirect, jsonify, url_for
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Playlist, PlaylistSong
app = Flask(__name__)

engine = create_engine('sqlite:///musicplaylist.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

from flask import session as login_session
import random, string

#oauth imports
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME ="Catalog"

@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

	 try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    #check if user already exists
    email = login_session['email']
    if session.query(User).filter_by(email=email).count():
        user_id = get_user_id(email)
    else:
    #add user to database
        user_id = create_user(login_session)
    
    login_session['user_id'] = user_id
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output
	
def create_user(login_session):
    newUser = User(name=login_session['username'], email=login_session['email'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

def get_user_id(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

@app.route('/gdisconnect')
def gdisconnect():
        # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/login')
def showLogin():
	state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
	login_session['state'] = state
	return render_template('login.html', STATE=state)
  


 

# Fake Restaurants
#playlist = {'name': 'uplifting music', 'id': '1'}

#playlists = [{'name': 'uplifting music', 'id': '1'}, {'name':'Romantic music', 'id':'2'},{'name':'Angry workout music', 'id':'3'},{'name':'Dance hits', 'id':'4'}] 


# Fake Playlist songs
#songs = [ {'name':'Rise up', 'artist':'Andra Day', 'time':'4.13','album' :'Cheers to the fall', 'id':'1'}, {'name':'thinking out loud','artist':'Ed Sheeran', 'time':'4.41', 'album':'X','id':'2'},{'name':'My time', 'artist':'fabolous','time':'4.35', 'album':'beauty','id':'3'},{'name':'Teach me how to dougie', 'artist':'cali swag district', 'time':'3.34', 'album':'Rap dance hits','id':'4'} ]
#song =  {'name':'Rise up','artist':'Andra Day','time':'4.13','album' :'Cheers to the fall'}
#songs = []

@app.route('/playlist/<int:playlist_id>/song/JSON')
def playlistJSON(playlist_id):
    playlist = session.query(Playlist).filter_by(id=playlist_id).one()
    songs = session.query(PlaylistSong).filter_by(
        playlist_id=playlist_id).all()
    return jsonify(PlaylistSongs=[s.serialize for s in songs])

@app.route('/playlist/<int:playlist_id>/song/<int:song_id>/JSON')
def playlistSongJSON(playlist_id, song_id):
    Playlist_Song = session.query(PlaylistSong).filter_by(id=menu_id).one()
    return jsonify(Playlist_Song=Playlist_Song.serialize)
    
@app.route('/playlist/JSON')
def playlistsJSON():
    playlists = session.query(playlist).all()
    return jsonify(playlists=[p.serialize for p in playlists])

#Show all playlist
@app.route('/')
@app.route('/playlist/')
def showPlaylists():
    playlists = session.query(Playlist).all()
    # return the page with all my playlists
    return render_template('playlists.html', playlists=playlists)
    
# Create a new playlist
@app.route('/playlist/new/', methods=['GET', 'POST'])
def newPlaylist():
    if request.method == 'POST':
        newPlaylist = Playlist(name=request.form['name'])
        session.add(newPlaylist)
        session.commit()
        return redirect(url_for('playlists'))
    else:
        return render_template('newPlaylist.html')
    # return "This page will be for making a new restaurant"
    
# Edit playlist

@app.route('/playlist/<int:playlist_id>/edit/', methods=['GET', 'POST'])
def editPlaylist(playlist_id):
    editedPlaylist = session.query(
        Playlist).filter_by(id=playlist_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedPlaylist.name = request.form['name']
            return redirect(url_for('playlists'))
    else:
        return render_template(
            'editPlaylist.html', playlist=editedPlaylist)

    # return "This page will be for editing a playlist"
    
@app.route('/playlist/<int:playlist_id>/delete/', methods=['GET', 'POST'])
def deletePlaylist(playlist_id):
    Playlisttobedeleted = session.query(
        Playlist).filter_by(id=playlist_id).one()
    if request.method == 'POST':
        session.delete(Playlisttobedeleted)
        session.commit()
        return redirect(
            url_for('playlists', playlist_id=playlist_id))
    else:
        return render_template(
            'deletePlaylist.html', playlist=Playlisttobedeleted)
            
# show a playlist song
@app.route('/playlist/<int:playlist_id>/')
@app.route('/playlist/<int:playlist_id>/song/')
def showPlaylistSong(playlist_id):
    restaurant = session.query(Playlist).filter_by(id=playlist_id).one()
    songs = session.query(PlaylistSong).filter_by(
        _id=playlist_id).all()
    return render_template('song.html', songs=songs, playlist=playlist)
    # return 'This page is a song from a playlist %s' % playlist_id
    
@app.route(
    '/playlist/<int:playlist_id>/song/new/', methods=['GET', 'POST'])
def newPlaylistSong(playlist_id):
    if request.method == 'POST':
        newSong = PlaylistSong(name=request.form['name'], description=request.form[
                           'artist'], time=request.form['time'], genre=request.form['genre'], playlist_id=playlist_id)
        session.add(newSong)
        session.commit()

        return redirect(url_for('showPlaylists', playlist_id=playlist_id))
    else:
        return render_template('newplaylistsong.html', playlist_id=playlist_id)
        
    return render_template('newplaylistSong.html', playlist=playlist)
    # return 'This page is for making a new menu item for restaurant %s'
    # %playlist_id

@app.route('/playlist/<int:playlist_id>/song/<int:song_id>/edit',
           methods=['GET', 'POST'])
def editPlaylistSong(playlist_id, song_id):
    editedSong = session.query(PlaylistSong).filter_by(id=song_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedSong.name = request.form['name']
        if request.form['artist']:
            editedItem.artist = request.form['artist']
        if request.form['time']:
            editedSong.time = request.form['time']
        if request.form['genre']:
            editedSong.genre = request.form['genre']
        session.add(editedSong)
        session.commit()
        return redirect(url_for('playlists', playlist_id=playlist_id))
    else:

        return render_template(
            'editplaylistsong.html', playlist_id=playlist_id, song_id=song_id, song=editedSong)

    # return 'This page is for editing information about song 
    
@app.route('/playlist/<int:playlist_id>/song/<int:song_id>/delete',
           methods=['GET', 'POST'])
def deletePlaylistSong(playlist_id, song_id):
    songtodelete = session.query(PlaylistSong).filter_by(id=song_id).one()
    if request.method == 'POST':
        session.delete(songtodelete)
        session.commit()
        return redirect(url_for('song', playlist_id=playlist_id))
    else:
        return render_template('deleteplaylistSong.html', song=songtodelete)
    # return "This page is for deleting a song


if __name__ == '__main__':
    app.debug = True
    app.run(host = '0.0.0.0', port = 8080)
