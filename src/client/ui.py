def ask_rounds():
    """gets input for number of rounds"""
    while True:
        try:
            val = input("How many rounds do you want to play? ").strip()
            num = int(val)
            if num > 0:
                return num
            print("Please enter a number > 0")
        except ValueError:
            print("That's not a number.")

def ask_name():
    """gets input for team name"""
    name = input("Enter your Team Name: ").strip()
    if not name:
        return "Team_Client"
    return name

def ask_hit_or_stand():
    """loops until user enters 'hit' or 'stand'"""
    while True:
        choice = input("Your move? (Hit/Stand): ").strip().lower()
        if choice.startswith('h'):
            return "hit"
        if choice.startswith('s'):
            return "stand"
        print("Invalid move. Please type 'hit' or 'stand'.")