#!/usr/bin/env python3

import requests
import base64
import collections

## GLOBALS
class printed_colors:
    SUCCESS = '\033[1:32m'
    FAILURE = '\033[1:31m'
    COMPLETE = '\033[1:33m'


CLIENT_ID = '7ac04f5446fe4349a3dc4faa6956413a'
CLIENT_SECRET = '204450a8541a459b8f8da9d94dc8f4a6'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
AUTH_URL = 'https://accounts.spotify.com/authorize'
BASE_URL = 'https://api.spotify.com/v1/'
REDIRECT_URI = 'https://open.spotify.com/collection/playlists'

USER = { 'brookemack910' : 'Comet110!' }

def get_access_token(scope_list):

    scope_spaces = ' '.join(item for item in scope_list)

    auth_data = { 'client_id': CLIENT_ID,
            'response_type': 'code',
            'redirect_uri': REDIRECT_URI,
            'scope': scope_spaces,
            }

    auth_code = requests.get(AUTH_URL, auth_data)
    print("Web Address: " + auth_code.history[0].url + "\n")

    auth_response = input("Authorization redirect code: ")
    print()

    client_creds = f"{CLIENT_ID}:{CLIENT_SECRET}"
    client_creds_b64 = base64.urlsafe_b64encode(client_creds.encode())

    headers = { 'Content-Type' : 'application/x-www-form-urlencoded',
            'Authorization': 'Basic {}'.format(client_creds_b64.decode())
            }

    token_data = { 'grant_type': 'authorization_code',
                'code': auth_response,
                'redirect_uri': REDIRECT_URI,
    }

    access_token_data = requests.post(url=TOKEN_URL, data=token_data, headers=headers).json()

    return access_token_data['access_token']

def get_artist_recs(access_token):

    headers = { 'Authorization' : 'Bearer {token}'.format(token=access_token) }
    users_artists = collections.defaultdict(dict)
    artist_recs = collections.defaultdict(dict)

    # Get user ID
    userID = get_user_ID(headers)

    # Get playlist info
    users_artists = get_playlist(headers, userID, users_artists)

    # Get liked albums
    users_artists = get_liked_albums(headers, userID, users_artists)

    # Get liked songs
    users_artists = get_liked_songs(headers, userID, users_artists)
    print("\n\n\n\n")

    # Sort dictionary
    users_artists = sorted(users_artists, key=users_artists.get, reverse=True)

    # Get artist recs based on top 25 artists
    artist_recs = generate_new_recs(headers, users_artists, artist_recs)

    # Sort dictionary
    artist_recs = sorted(artist_recs.items(), key=lambda p: p[1], reverse=True)

    # Print top 20 new recommendations
    print_new_recs(headers, artist_recs)

def get_user_ID(headers):

    user_profile_url = BASE_URL + 'me'
    user_profile_json = requests.get(user_profile_url, headers=headers)
    print(user_profile_json)
    user_profile_json = user_profile_json.json()
    return user_profile_json['id']


def get_playlist(headers, userID, users_artists):

    user_playlist_url = BASE_URL + 'me/playlists'
    user_playlist_json = requests.get(user_playlist_url, headers=headers).json()
    next = True

    while next :
        for item in user_playlist_json['items'] :
            if item['owner']['id'] != userID :
                continue
            else :
                get_playlist_tracks(headers, item['id'], users_artists)

        user_playlist_json = get_next_url(user_playlist_json, headers)
        if not user_playlist_json:
            next = False

    return users_artists


def get_playlist_tracks(headers, playlistID, users_artists):

    playlist_url = BASE_URL + 'playlists/' + playlistID + '/tracks'
    playlist_json = requests.get(playlist_url, headers=headers).json()
    next = True

    while next :
        for item in playlist_json['items'] :
            append_artist_id(item, users_artists)

        playlist_json = get_next_url(playlist_json, headers)
        if not playlist_json:
            next = False

    return users_artists

def get_liked_albums(headers, userID, users_artists):

    user_album_url = BASE_URL + 'me/albums'
    user_album_json = requests.get(user_album_url, headers=headers).json()
    next = True

    while next :
        for item in user_album_json['items']:
            artist_id = item['album']['artists'][0]['id']
            artist_name = item['album']['artists'][0]['name']
            if users_artists[artist_id] :
                print('Artist Previously Added: ' + artist_name)
                users_artists[artist_id] += 1
            else :
                print('Artist Added: ' + artist_name)
                users_artists[artist_id] = 1

        user_album_json = get_next_url(user_album_json, headers)
        if not user_album_json:
            next = False

    return users_artists


def get_liked_songs(headers, userID, users_artists):

    user_track_url = BASE_URL + 'me/tracks'
    user_track_json = requests.get(user_track_url, headers=headers).json()
    next = True

    while next :
        for item in user_track_json['items']:
            append_artist_id(item, users_artists)

        user_track_json = get_next_url(user_track_json, headers)
        if not user_track_json:
            next = False

    return users_artists

def append_artist_id(item, users_artists):

    artist_id = item['track']['artists'][0]['id']
    artist_name = item['track']['artists'][0]['name']
    if users_artists[artist_id] :
        print('Artist Previously Added: ' + artist_name)
        users_artists[artist_id] += 1
    else :
        print('Artist Added: ' + artist_name)
        users_artists[artist_id] = 1

def get_next_url(given_json, headers):

    new_json = None

    if given_json['next']:
        next = given_json['next']
        new_json = requests.get(next, headers=headers).json()

    return new_json

def generate_new_recs(headers, users_artists, artist_recs):

    for count, artist_id in enumerate(users_artists):
        if count == 25: break

        new_artist_url = BASE_URL + 'artists/' + artist_id + '/related-artists'
        new_artist_json = requests.get(new_artist_url, headers=headers).json()

        for item in new_artist_json['artists']:
            if item['id'] in users_artists: continue
            if artist_recs[item['id']] :
                print('Artist Previously Added: ' + item['name'])
                artist_recs[item['id']] += 1
            else :
                print('Artist Added: ' + item['name'])
                artist_recs[item['id']] = 1

    return artist_recs

def print_new_recs(headers, artist_recs):

    print("\n\n\n\n")

    for count, artist_id in enumerate(artist_recs, 1):
        if count == 21: break

        artist_url = BASE_URL + 'artists/' + artist_id[0]
        artist_json = requests.get(artist_url, headers=headers).json()

        print(str(count) + '. ' + artist_json['name'] + ' (' + str(artist_id[1]) + ')')


def main():

    scope_list = ["user-library-read", "playlist-read-private", "user-top-read", "playlist-read-collaborative", "user-read-private", "user-read-email"]
    access_token = get_access_token(scope_list)
    print("Access Token: " + access_token + "\n")

    get_artist_recs(access_token)


if __name__ == '__main__':
    main()
