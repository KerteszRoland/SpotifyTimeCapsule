import main as main
import urllib3 
import urllib.parse as parse
from flask import Flask, request, render_template, make_response, redirect
from flask_cors import CORS, cross_origin
import uuid
from cryptography.fernet import Fernet
app = Flask(__name__)
CORS(app, resources={r"/login": {"origins":"*"}}, support_credentials=True)

users = {}
SECRET = Fernet(Fernet.generate_key())
TESTING = False


def EncryptToken(string_token):
    byte_token = bytes(string_token, encoding="utf-8")
    encrypted = SECRET.encrypt(byte_token)
    return encrypted
    
    
def DecryptToken(byte_token):
    decrypted = SECRET.decrypt(byte_token).decode('utf-8')
    return decrypted


def CreateSession(sid, token):
    users[sid] = EncryptToken(token)


def SetCookie(resp):
    resp.set_cookie("sid", str(uuid.uuid1().int), httponly=True, secure=False, path="/")
    return resp


def IsLoggedIn(request):
    sid = request.cookies.get("sid")
    logged_in = sid in users.keys()
    return logged_in


@app.route("/", methods=["GET"])
def root():
    if IsLoggedIn(request):
       return redirect("/dashboard")
    else:
        return redirect("/login")


@app.route("/login", methods=["GET"])
def Login(): 
    if IsLoggedIn(request):
        return redirect("/dashboard")
    else:
        resp =  make_response(render_template("login.html"))
        SetCookie(resp)
        return resp
        

@app.route("/dashboard", methods=["GET"])
def Dashboard():
    code = request.args.get("code")
    sid = request.cookies.get("sid")
    
    if code:
         try:
            token = main.GetToken(code)
         except main.spotipy.oauth2.SpotifyOauthError:
            return redirect("/login")
            
         CreateSession(sid, token)
         return redirect("/dashboard")
    else:
        if not IsLoggedIn(request):
            return redirect("/login")
       
    
    resp = make_response(render_template("dashboard.html"))
    return resp


@app.route("/api/save_liked_songs", methods=["GET"])
def SaveLikedSongsToPlaylist():
    if not IsLoggedIn(request):
        return {
            "status": "error",
            "description": "INVALID SID"
        }
    if TESTING:
        print("..........SAVING LIKED SONGS TO PLAYLIST..........")
    else:
        sid = request.cookies.get("sid")
        token = DecryptToken(users[sid])
        sp = main.GetSP(token)
        main.SaveLikedSongsToPlaylist(sp)
    
    return {"status": "ok"}


@app.route("/api/create_time_capsule", methods=["GET"])
def CreateTimeCapsule():
    if not IsLoggedIn(request):
        return {
            "status": "error",
            "description": "INVALID SID"
        }
    if TESTING:
        print("..........CREATING TIME CAPSULE..........")
    else:
        sid = request.cookies.get("sid")
        token = DecryptToken(users[sid])
        sp = main.GetSP(token)
        main.SavedTracksToPlaylistsByMonth(sp)
    
    return {"status": "ok"}


@app.route("/api/save_discover_weekly", methods=["GET"])
def SaveDiscoverWeekly():
    if not IsLoggedIn(request):
        return {
            "status": "error",
            "description": "INVALID SID",
            "error": "invalid_sid"
        }
    if TESTING:
        print("..........SAVING DISCOVER WEEKLY..........")
        resp = {"status": "ok"}
        return resp
    else:
        sid = request.cookies.get("sid")
        token = DecryptToken(users[sid])
        sp = main.GetSP(token)
        playing_playlist = main.GetCurrentPlayingPlaylist(sp)
        if playing_playlist == None:
            resp = {
            "status": "error",
            "description": "This isn't a playlist",
            "error": "not_playlist"
            }
            return resp
        playing_playlist_name = playing_playlist["name"] 
        print(f"Playlist name: {playing_playlist_name}")
        if playing_playlist_name != "Discover Weekly":
            resp = {
            "status": "error",
            "description": "This playlist isn't Discover Weekly!",
            "error": "not_discover_weekly"
            }
        else:    
            playlist_id = main.GetCurrentPlayingPlaylistID(sp)
            new_playlist_id = main.SaveDiscoverWeekly(sp, playlist_id)
            resp = {
            "status": "ok",
            "playlist_url": f"https://open.spotify.com/playlist/{new_playlist_id}?si=8998205cd0f54cef"
            }
        return resp


def TestEncrypting():
    message = "DOGE TO THE MOON"
    print(message)
    encrypted = EncryptToken(message)
    print(encrypted)
    print(DecryptToken(encrypted))


if __name__ == "__main__":
    app.run(threaded=True, port=80)
