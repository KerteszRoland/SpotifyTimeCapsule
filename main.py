import spotipy
from spotipy.oauth2 import SpotifyOAuth
from datetime import datetime


def GetClientSecret():
    with open("client_secret.txt", "r") as file:
        return file.readline().strip()


def GetClientID():
    with open("client_id.txt", "r") as file:
        return file.readline().strip()


CLIEND_ID = GetClientID()
CLIENT_SECRET = GetClientSecret()

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIEND_ID,
                                               client_secret=CLIENT_SECRET,
                                               redirect_uri="https://orangethereal.hu",
                                               scope=["playlist-modify-public","user-library-read"]))


def GetTrackAddedMonth(track):
    return int(track['added_at'].split("-")[1])


def GetTrackId(track):
    return track['track']['id']


def GetSavedTracks(offset=0):
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
    
    
def CreatePlaylist(name):
    user = sp.current_user()["id"]
    playlist_info = sp.user_playlist_create(user, name, public=True, collaborative=False, description='')
    return playlist_info["id"]
    
    
def AddTracksToPlaylist(playlist_id, track_ids):
    user_id = sp.current_user()["id"]
    sp.user_playlist_add_tracks(user_id, playlist_id, track_ids)
    
  
def CreateMonthlyPlaylist():
    from datetime import datetime
    date = datetime.today()
    month_name = "{0:%B}".format(date)
    playlist_id = CreatePlaylist("{0.year} {0:%B}".format(date))
    track_ids = GetMonthTracks(date.month)
    AddTracksToPlaylist(playlist_id, track_ids)


def GetAllSavedTracks():
    tracks = []
    response = sp.current_user_saved_tracks(limit=50, offset=0)
    while response["next"] is not None:
        tracks.extend(response["items"])
        print(response["next"])
        offset = response["next"].split("offset=")[1].split("&limit")[0]
        response = sp.current_user_saved_tracks(limit=50, offset=offset)
    
    tracks.extend(response["items"])
    return tracks
    
    
def SavedTracksToPlaylistsByMonth():
    all_tracks = GetAllSavedTracks()
    all_tracks.reverse()
    
    previous_date = datetime.today()
    previous_playlist_id = ""
    
    temp_track_ids = []
    for track in all_tracks:
        added_date = datetime.strptime(track["added_at"].split("T")[0], '%Y-%m-%d')
        if added_date.month == datetime.today().month and added_date.year == datetime.today().year:
            AddTracksToPlaylist(previous_playlist_id, temp_track_ids)
            break
        if added_date.month != previous_date.month or added_date.year != previous_date.year:
            if len(temp_track_ids) > 0:
                AddTracksToPlaylist(previous_playlist_id, temp_track_ids)
            temp_track_ids = []
            previous_playlist_id = CreatePlaylist("{0.year} {0:%B}".format(added_date))
            previous_date = added_date

        temp_track_ids.append(track["track"]["id"])
    
 
def SaveLikedSongsToPlaylist():
    import math
    all_tracks = GetAllSavedTracks()
    track_ids = [x["track"]["id"] for x in all_tracks]
    playlist_id = CreatePlaylist("Liked Songs")
    for i in range(math.ceil(len(all_tracks)/100)):
        if len(track_ids) >= 100:
            temp_tracks = track_ids[:100]
        else:
            temp_tracks = track_ids
        AddTracksToPlaylist(playlist_id, temp_tracks)
        track_ids = track_ids[100:]
    

def SaveDiscoveryWeekly(playlist_id):
    user_id = sp.current_user()["id"]
    tracks = sp.user_playlist_tracks(user_id, playlist_id)["items"]
    track_ids = [x["track"]["id"] for x in tracks]
    saved_playlist_id = CreatePlaylist("{0.year} {0:%V}".format(datetime.today()))
    AddTracksToPlaylist(saved_playlist_id, track_ids)

