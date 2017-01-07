from flask import Flask, render_template, flash, request, redirect, jsonify, url_for
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Playlist, PlaylistSong
from flask import session as login_session
import random, string

#oauth imports
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
	open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME ="Playlist catalog project"

engine = create_engine('sqlite:///musicplaylist.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)
	

@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.4/me"
    # strip expire tag from access token
    token = result.split("&")[0]


    url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout, let's strip out the information before the equals sign in our token
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # Get user picture
    url = 'https://graph.facebook.com/v2.4/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'])
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"




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
	return response

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
            json.dumps("Token's client ID does not match app's."), 200)
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

def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user
    
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



  


 


#playlist = {'name': 'uplifting music', 'id': '1'}

#playlists = [{'name': 'uplifting music', 'id': '1'}, {'name':'Romantic music', 'id':'2'},{'name':'Angry workout music', 'id':'3'},{'name':'Dance hits', 'id':'4'}] 



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
    Playlist_Song = session.query(PlaylistSong).filter_by(id=song_id).one()
    return jsonify(Playlist_Song=Playlist_Song.serialize)
    
@app.route('/playlist/JSON')
def playlistsJSON():
    playlists = session.query(Playlist).all()
    return jsonify(playlists=[p.serialize for p in playlists])

#Show all playlist
@app.route('/')
@app.route('/playlist/')
def showPlaylists():
    playlists = session.query(Playlist).all()
    if 'username' not in login_session:
        return render_template('login.html')
    else:
        return render_template('playlists.html', playlists=playlists)
    
    
# Create a new playlist
@app.route('/playlist/new/', methods=['GET', 'POST'])
def newPlaylist():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newPlaylist = Playlist(name=request.form['name'], user_id=login_session['user_id'])
        session.add(newPlaylist)
        flash('New Store %s Successfully Created' % newplaylist.name)
        session.commit()
        return redirect(url_for('showPlaylists'))
    else:
        return render_template('newPlaylist.html')
    
    
# Edit playlist

@app.route('/playlist/<int:playlist_id>/edit/', methods=['GET', 'POST'])
def editPlaylist(playlist_id):
    editedPlaylist = session.query(
        Playlist).filter_by(id=playlist_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if editedPlaylist.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to edit this playlist. Please create your own playlist in order to edit.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            editedPlaylist.name = request.form['name']
            flash('Playlist Successfully Edited %s' % editedRestaurant.name)
            return redirect(url_for('showPlaylists'))
    else:
        return render_template('editPlaylist.html', playlist=editedPlaylist)

    # return "This page will be for editing a playlist"
    
@app.route('/playlist/<int:playlist_id>/delete/', methods=['GET', 'POST'])
def deletePlaylist(playlist_id):
    Playlisttobedeleted = session.query(
        Playlist).filter_by(id=playlist_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if Playlisttobedeleted.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to delete this playlist. Please create your own playlist in order to delete.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(Playlisttobedeleted)
        flash('%s Successfully Deleted' % Playlisttobedeleted.name)
        session.commit()
        return redirect(url_for('showplaylists', playlist_id=playlist_id))
    else:
        return render_template('deletePlaylist.html', playlist=Playlisttobedeleted)
            
# show a playlist song
@app.route('/playlist/<int:playlist_id>/')
@app.route('/playlist/<int:playlist_id>/song/')
def Song(playlist_id):
    playlist = session.query(Playlist).filter_by(id=playlist_id).one()
    creator = getUserInfo(playlist.user_id)
    songs = session.query(PlaylistSong).filter_by(
        playlist_id=playlist_id).all()
    if 'username' not in login_session or creator.id != login_session['user_id']:
        return redirect('/login')
    else: 
        return render_template('song.html', songs=songs, playlist=playlist)
# return 'This page is a song from a playlist %s' % playlist_id
    
@app.route('/playlist/<int:playlist_id>/song/new/', methods=['GET', 'POST'])
def newPlaylistSong(playlist_id):
    if 'username' not in login_session:
        return redirect('/login')
    playlist = session.query(Playlist).filter_by(playlist_id=playlist_id).one()
    if login_session['user_id'] != store.user_id:
        return "<script>function myFunction() {alert('You are not authorized to add menu songs. Please create your own account to add songs');}</script><body onload='myFunction()''>"
        if request.method == 'POST':
            newSong = PlaylistSong(name=request.form['name'], description=request.form[
                           'artist'], time=request.form['time'], genre=request.form['genre'], playlist_id=playlist_id)
        session.add(newSong)
        session.commit()
        flash('New song %s Successfully added' % (newItem.name))
        return redirect(url_for('showPlaylists', playlist_id=playlist_id))
    else:
        return render_template('newplaylistsong.html', playlist_id=playlist_id)
        

    # return 'This page is for adding a new song to the library %s' %playlist_id

@app.route('/playlist/<int:playlist_id>/song/<int:song_id>/edit', methods=['GET', 'POST'])
def editPlaylistSong(playlist_id, song_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedSong = session.query(PlaylistSong).filter_by(id=song_id).one()
    playlist = session.query(Playlist).filter_by(id=playlist_id).one()
    if login_session['user_id'] != playlist.user_id:
        return "<script>function myFunction() {alert('You are not authorized to edit song info on this playlist. Please create your own playlist in order to edit items.');}</script><body onload='myFunction()''>"
        return redirect('/login')
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
        return render_template('editplaylistsong.html', playlist_id=playlist_id, song_id=song_id, song=editedSong)

    # return 'This page is for editing information about song 
    
@app.route('/playlist/<int:playlist_id>/song/<int:song_id>/delete',methods=['GET', 'POST'])
def deletePlaylistSong(playlist_id, song_id):
    if 'username' not in login_session:
        return redirect('/login')
    playlist = session.query(Playlist).filter_by(id=playlist_id).one()
    songtodelete = session.query(PlaylistSong).filter_by(id=song_id).one()
    if login_session['user_id'] != playlist.user_id:
        return "<script>function myFunction() {alert('You are not authorized to delete songs. Please create your own playlist in order to delete songs.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(songtodelete)
        session.commit()
        flash('Song Successfully Deleted')
        return redirect(url_for('song', playlist_id=playlist_id))
    else:
        return render_template('deleteplaylistSong.html', song=songtodelete)
 # return "This page is for deleting a song
    
 #Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['credentials']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showStore'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showStores'))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host = '0.0.0.0', port = 8080)
