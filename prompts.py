
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
