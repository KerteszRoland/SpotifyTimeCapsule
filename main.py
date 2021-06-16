import spotipy
from spotipy.oauth2 import SpotifyOAuth
from datetime import datetime


def GetClientSecret():
    with open("client_secret.txt", "r") as file:
        return file.readline().strip()


def GetClientID():
    with open("client_id.txt", "r") as file:
        return file.readline().strip()


CLIENT_ID = GetClientID()
CLIENT_SECRET = GetClientSecret()

def GetTestSP():
    scopes=["playlist-modify-public","user-library-read", "user-read-private", "user-read-currently-playing", "user-read-playback-state", "user-modify-playback-state"]
    
    OAuth = spotipy.oauth2.SpotifyOAuth(
    client_id=CLIENT_ID, 
    client_secret=CLIENT_SECRET, 
    redirect_uri="http://localhost:8080",
    show_dialog=True,
    scope=scopes,
    open_browser=True)
    
    sp = spotipy.client.Spotify(oauth_manager=OAuth)
    return sp

def GetSP(token):
    scopes=["playlist-modify-public","user-library-read", "user-read-private", "user-read-currently-playing", "user-read-playback-state", "user-modify-playback-state"]
    
    OAuth = spotipy.oauth2.SpotifyOAuth(
    client_id=CLIENT_ID, 
    client_secret=CLIENT_SECRET, 
    redirect_uri="http://localhost/dashboard",
    show_dialog=False,
    scope=scopes,
    open_browser=False)
    
    sp = spotipy.client.Spotify(auth=token, oauth_manager=OAuth)
    return sp

def GetToken(code):
    scopes=["playlist-modify-public","user-library-read", "user-read-private", "user-read-currently-playing", "user-read-playback-state", "user-modify-playback-state"]
    
    OAuth = spotipy.oauth2.SpotifyOAuth(
    client_id=CLIENT_ID, 
    client_secret=CLIENT_SECRET, 
    redirect_uri="http://localhost/dashboard",
    show_dialog=False,
    scope=scopes,
    open_browser=False)
    
    access_token = OAuth.get_access_token(code=code, as_dict=False, check_cache=False)
    return access_token
    
    
def GetTrackAddedMonth(track):
    return int(track['added_at'].split("-")[1])


def GetTrackId(track):
    return track['track']['id']


def GetSavedTracks(sp, offset=0):
    saved_tracks = sp.current_user_saved_tracks(limit=50, offset=offset)
    return saved_tracks["items"]


def GetMonthTracks(month_number):
    track_ids = []
    saved_tracks = GetSavedTracks()
    last_track = saved_tracks[-1]
    if GetTrackAddedMonth(last_track) == month_number:
        next_tracks = GetSavedTracks(50)
        saved_tracks.extend(next_tracks)
    for item in saved_tracks:
        if GetTrackAddedMonth(item) == month_number:
            track_ids.append(GetTrackId(item))
        else:
            break
        
    return track_ids
    
    
def CreatePlaylist(sp, name):
    user = sp.current_user()["id"]
    playlist_info = sp.user_playlist_create(user, name, public=True, collaborative=False, description='')
    return playlist_info["id"]
    
    
def AddTracksToPlaylist(sp, playlist_id, track_ids):
    user_id = sp.current_user()["id"]
    sp.user_playlist_add_tracks(user_id, playlist_id, track_ids)
    
  
def CreateMonthlyPlaylist():
    from datetime import datetime
    date = datetime.today()
    month_name = "{0:%B}".format(date)
    playlist_id = CreatePlaylist("{0.year} {0:%B}".format(date))
    track_ids = GetMonthTracks(date.month)
    AddTracksToPlaylist(playlist_id, track_ids)


def GetAllSavedTracks(sp):
    tracks = []
    response = sp.current_user_saved_tracks(limit=50, offset=0)
    while response["next"] is not None:
        tracks.extend(response["items"])
        print(response["next"])
        offset = response["next"].split("offset=")[1].split("&limit")[0]
        response = sp.current_user_saved_tracks(limit=50, offset=offset)
    
    tracks.extend(response["items"])
    return tracks
    
    
def SavedTracksToPlaylistsByMonth(sp):
    all_tracks = GetAllSavedTracks(sp)
    all_tracks.reverse()
    
    previous_date = datetime.today()
    previous_playlist_id = ""
    
    temp_track_ids = []
    for track in all_tracks:
        added_date = datetime.strptime(track["added_at"].split("T")[0], '%Y-%m-%d')
        if added_date.month == datetime.today().month and added_date.year == datetime.today().year:
            AddTracksToPlaylist(sp, previous_playlist_id, temp_track_ids)
            break
        if added_date.month != previous_date.month or added_date.year != previous_date.year:
            if len(temp_track_ids) > 0:
                AddTracksToPlaylist(sp, previous_playlist_id, temp_track_ids)
            temp_track_ids = []
            previous_playlist_id = CreatePlaylist(sp, "{0.year} {0:%B}".format(added_date))
            previous_date = added_date

        temp_track_ids.append(track["track"]["id"])


def SaveLikedSongsToPlaylist(sp):
    import math
    all_tracks = GetAllSavedTracks(sp)
    track_ids = [x["track"]["id"] for x in all_tracks]
    playlist_id = CreatePlaylist(sp, "Liked Songs")
    for i in range(math.ceil(len(all_tracks)/100)):
        if len(track_ids) >= 100:
            temp_tracks = track_ids[:100]
        else:
            temp_tracks = track_ids
        AddTracksToPlaylist(sp, playlist_id, temp_tracks)
        track_ids = track_ids[100:]
    

def SaveDiscoverWeekly(sp, playlist_id):
    user_id = sp.current_user()["id"]
    tracks = sp.user_playlist_tracks(user_id, playlist_id)["items"]
    track_ids = [x["track"]["id"] for x in tracks]
    saved_playlist_id = CreatePlaylist(sp, "{0.year} {0:%V}".format(datetime.today()))
    AddTracksToPlaylist(sp, saved_playlist_id, track_ids)
    return saved_playlist_id

def GetCurrentPlayingSong(sp):
    return sp.current_user_playing_track()

def GetCurrentPlayingSongName(sp):
    song = GetCurrentPlayingSong(sp)
    artists_names = ", ".join([x["name"] for x in song["item"]["artists"]])
    print(f'Playlist ID: {song["context"]["href"].split("/")[-1]}')
    return f'{artists_names} - {song["item"]["name"]}'


def GetPlaylist(sp, playlist_id):
    return sp.playlist(playlist_id)
    

def GetCurrentPlayingPlaylist(sp):
    song = GetCurrentPlayingSong(sp)
    try:
        if song["context"]["type"] == "playlist":
            playlist_id = song["context"]["href"].split("/")[-1]
            playlist = GetPlaylist(sp, playlist_id)
            return playlist
        else:
            return None
    except TypeError:
        return None


def GetCurrentPlayingPlaylistID(sp):
    playlist_id = GetCurrentPlayingPlaylist(sp)["id"]
    return playlist_id


def GetActiveDevice(sp):
    device = [x for x in sp.devices()["devices"] if x["is_active"] == True]
    return device[0]


def SetVolume(sp, volume_percent):
    device_id = GetActiveDevice()["id"]
    sp.volume(volume_percent, device_id=device_id)
    

def GetUserInfo(sp):
    return sp.current_user()


def GetUserName(sp):
    return GetUserInfo(sp)["display_name"] 


def GetUserImageURL(sp):
    return GetUserInfo(sp)["images"][0]["url"]


"""
sp = GetTestSP()
user_info = GetUserInfo(sp)
import json
playlist_id = GetCurrentPlayingPlaylistID(sp)
SaveDiscoverWeekly(sp, playlist_id)
"""
