
from os import environ as env
from dotenv import load_dotenv
load_dotenv()

def places_filter(user_interests):
    # open file with each place type in one line, add to list
    with open("places-types.txt", "r") as f:
        place_types = f.read().splitlines()

    prompt  = f"""
    These and only these place types are supported:

    place_types: {', '.join(place_types)}

    --

    The user interests are: {', '.join(user_interests)}
    --

    Now, be very objective, and provide a list of up to 10 place types that matches the user's interests.
    Never include a place type that is not in the place_types list.
    Only the list, no additional explanations. Use a simple JSON array as the response.
    Please provide the list of categories without using any markdown formatting, code blocks, or any extra characters.
    """

    return prompt

def adjust_places(user_interests, places_from_maps, latlon, radius):
    return f"""
    The user interests are: {', '.join(user_interests)}

    The places from the maps are: {places_from_maps}

    Are there places that are highly relevant to the user interests that are missing from the list?
    Are there places that are not relevant to the user interests that are in the list?

    Remember that the user is at latlon {latlon} and the radius is {radius}.

    Adjust the list of places to match the user interests (add or remove places as needed).

    Return a JSON array with up to {len(places_from_maps)} places that should be included in the list.
    Sort it by relevance as a global landmark.
    No additional explanations, no markup, just the JSON array.
    Please provide the list of categories without using any markdown formatting, code blocks, or any extra characters.
    """

def guide_instructions(user_interests, latlon, radius, nearby_places):
    return f"""
    You are an expert tourist guide (female).
    You are friendly and have a soft voice, people love to hear you explaining about all sorts of attractions.

    Here are the interests of your client: {user_interests}

    The client is at latlon {latlon}, which has these nearby places (radius of {radius}): {nearby_places}

    Generate 30 seconds of speech script that will satisfy your client.
    Note a few special tips that you must follow:
    - avoid being generic
    - try to focus on interesting things that are concrete
    - be humorous (fit a joke if it makes sense)

    Output language: {env["LANGUAGE"]}
    """

def guide_instructions_one_place(user_interests, latlon, place, continuation=False):
    continuation_text = "Remember that you are continuing speech that you started earlier about a different but nearby place." if continuation else ""

    return f"""
    You are an expert tourist guide (female).
    You are friendly and have a soft voice, people love to hear you explaining about all sorts of attractions.

    Here are the interests of your client: {user_interests}

    The client is close to {place} at latlon {latlon}.

    Generate 30 seconds of speech script about this place ({place}), that will satisfy your client.

    {continuation_text}

    Note a few special tips that you must follow:
    - be specific rather than generic
    - focus on interesting things that are concrete
    - be humorous (fit a joke if it makes sense)

    Output language: {env["LANGUAGE"]}
    """
