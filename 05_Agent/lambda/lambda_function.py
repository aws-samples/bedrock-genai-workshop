import requests 
from igdb.wrapper import IGDBWrapper
import os
import json
from google.protobuf.json_format import MessageToJson, MessageToDict
from igdb.igdbapi_pb2 import GameResult, GenreResult, CoverResult, GameVideoResult
import datetime

igdb_api_client_id = os.environ.get("IGDB_CLIENT_ID", "not found")
igdb_api_access_token = os.environ.get("IGDB_ACCESS_TOKEN", "not found")
wrapper = IGDBWrapper(igdb_api_client_id,  igdb_api_access_token)
print(f"credentials: igdb_api_client: {igdb_api_client_id} igdb_api_access_token: {igdb_api_access_token}")

PLAYSATTION_PLATFORM_IDS = "(8, 38, 9, 46, 48, 167, 7, 441, 390, 165)" # These are pre calculated for Playstation platforms

def find_value_from_param(parameters, name):
    for param in parameters:
        if param['name'] == name:
            return param['value']
    return "None"
        
def get_genres():
    byte_array = wrapper.api_request(
                'genres.pb',
                'fields name;'
              )
    genres_message = GenreResult()
    genres_message.ParseFromString(byte_array) # Fills the protobuf message object with the response
    response = MessageToDict(genres_message, preserving_proto_field_name = True)
    genres  = response['genres']
    return genres

def find_games(genre_id, rel_year):
    rel_year = int(rel_year)
    epoch_start = datetime.date(rel_year, 1, 1).strftime('%s')
    epoch_end = datetime.date(rel_year, 12, 31).strftime('%s')
    query = f'fields name, rating; where genres = {genre_id} & release_dates.date >= {epoch_start} & release_dates.date <= {epoch_end} & platforms = {PLAYSATTION_PLATFORM_IDS} ;'
    print(f"query is: {query}")
    byte_array = wrapper.api_request(
                'games.pb',
                query
              )
    games_message = GameResult()
    games_message.ParseFromString(byte_array) # Fills the protobuf message object with the response
    response = MessageToDict(games_message, preserving_proto_field_name = True)
    games  = response['games']
    return games
    
def get_game_cover(game_id):
    query = f'fields url; where game = {game_id};'
    print(f"query is: {query}")
    byte_array = wrapper.api_request(
                'covers.pb',
                query
              )
    covers_message = CoverResult()
    covers_message.ParseFromString(byte_array) # Fills the protobuf message object with the response
    response = MessageToDict(covers_message, preserving_proto_field_name = True)
    cover  = response['covers'][0]
    cover['mediaType'] = "image"
    return cover

def get_game_video(game_id):
    query = f'fields video_id; where game = {game_id};'
    print(f"query is: {query}")
    byte_array = wrapper.api_request(
                'game_videos.pb',
                query
              )
    message = GameVideoResult()
    message.ParseFromString(byte_array) # Fills the protobuf message object with the response
    response = MessageToDict(message, preserving_proto_field_name = True)
    print(f"response: {response}")
    if len(response['gamevideos']) > 0:
        item  = response['gamevideos'][0]
        item['mediaType'] = "video"
        item['url'] = item['video_id']
        item.pop('video_id') # make it consistent with the response payload for both image and video media
    else:
        item =  {}
    return item
    
def lambda_handler(event, context):

    response_body = {
        'application/json': {
            'body': "sample response"
        }
    }
    print(event)
    response = {}
    if event['apiPath'] == '/genres':
        response = get_genres()
    if event['apiPath'] == '/games':
        rel_year = find_value_from_param(event['parameters'], "releaseYear")
        genre_id = find_value_from_param(event['parameters'], "genreId")
        response = find_games(genre_id, rel_year)
    # if event['apiPath'] == "/images/{gameId}":
    #     game_id = find_value_from_param(event['parameters'], "gameId")
    #     response = get_game_cover(game_id)
    # if event['apiPath'] == "/videos/{gameId}":
    #     game_id = find_value_from_param(event['parameters'], "gameId")
    #     response = get_game_video(game_id)
    if event['apiPath'] == "/game-media":
        game_id = find_value_from_param(event['parameters'], "gameId")
        media_type = find_value_from_param(event['parameters'], "mediaType")
        if media_type == "image":
            response = get_game_cover(game_id)
        elif media_type == "video":
            response = get_game_video(game_id)
        else:
            respnose = "unsupported mediaType"
    
    response_body = {
    'application/json': {
        'body': response 
        }
    }
    print(f"response body: {response_body}")
    action_response = {
        'actionGroup': event['actionGroup'],
        'apiPath': event['apiPath'],
        'httpMethod': event['httpMethod'],
        'httpStatusCode': 200,
        'responseBody': response_body
    }
    
    session_attributes = event['sessionAttributes']
    prompt_session_attributes = event['promptSessionAttributes']
    
    api_response = {
        'messageVersion': '1.0', 
        'response': action_response,
        'sessionAttributes': session_attributes,
        'promptSessionAttributes': prompt_session_attributes
    }
    return api_response

