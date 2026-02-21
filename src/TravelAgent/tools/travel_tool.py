from random import randint

def get_random_destination() -> str:
    """Get a random vacation destination
    
    Returns:
        str: A randomly selected destination from our predefined list
    """
    destinations = [
        "Barcelona, Spain",
        "Paris, France", 
        "Berlin, Germany",
        "Tokyo, Japan",
        "Sydney, Australia",
        "New York, USA",
        "Cairo, Egypt",
        "Cape Town, South Africa",
        "Rio de Janeiro, Brazil",
        "Bali, Indonesia"
    ]
    return destinations[randint(0, len(destinations) - )]

"""
An example to show if a task can be handled by a simple function, use a function to don't overcomplicate it with an agent or overload the agent with unnecessary work.
"""