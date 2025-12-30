from random import randint

def get_random_destination() -> str:
    """Get a random vacation destination
    
    Returns:
        str: A randomly selected destination from our predefined list
    """
    # List of popular vacation destinations around the world
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
    # Return a random destination from the list
    return destinations[randint(0, len(destinations) - 1)]



# NOTE: 
"""
if a task can be done by a function , use the function , the simple way of doing it , not agent to complicated the task or overloads the agent 
"""