
def places_filter(user_interests):
    # open file with each place type in one line, add to list
    with open("places-types.txt", "r") as f:
        place_types = f.read().splitlines()

    prompt  = f"""
    These and only these place types are supported:

    {', '.join(place_types)}

    --

    The user interests are: {', '.join(user_interests)}
    --

    Now, be very objective, and provide a list of up to 10 place types that matches the user's interests.
    Only the list, no additional explanations. Use a simple JSON array as the response.
    """

    return prompt

def guide_instructions(user_interests, latlon, radius, nearby_places):
    return f"""
    You are an expert tourist guide (female).
    You are friendly and have a soft voice, people love to hear you explaining about all sorts of attractions.

    Here are the interests of your client: {user_interests}

    The client is at latlon {latlon}, which has these nearby places (radius of {radius}): {nearby_places}

    Generate 1 minute of speech script that will satisfy your client.
    Note a few special tips that you must follow:
    - avoid being generic
    - try to focus on interesting things that are concrete
    - be humorous (fit a joke if it makes sense)
    """
