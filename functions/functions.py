import random
import string

def generate_token(length=100):
    """
    Generates a random token consisting of Latin letters (both uppercase and lowercase)
    and digits. The token will have a length specified by the 'length' parameter.

    Args:
        length (int): The length of the token to be generated. Default is 200.

    Returns:
        str: A randomly generated token.

    Example:
        token = generate_token(50)
        print(token)  # Example output: 'aB3dE9FgHj2K1LmNo4P5QrStUvWxYzZ8A0bCdEfGhIj'

    Notes:
        - The function uses the `random.choices` method for efficient random selection.
        - The pool of characters includes lowercase and uppercase English letters and digits.
    """
    characters = string.ascii_letters + string.digits
    token = ''.join(random.choices(characters, k=length))
    return token