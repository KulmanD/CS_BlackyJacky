# gets input for number of rounds
def ask_rounds():
    while True:
        try:
            val = input("How many rounds do you want to play? ").strip()
            num = int(val)
            if num > 0:
                return num
            print("Please enter a number > 0")
        except ValueError:
            print("That's not a number.")


# gets input for team name
def ask_name():
    name = input("Enter your Team Name: ").strip()
    if not name:
        return "Team_Client"
    return name


# loops until user enters 'hit' or 'stand'
def ask_hit_or_stand():
    while True:
        choice = input("Your move? (Hit/Stand): ").strip().lower()
        if choice.startswith('h'):
            return "hit"
        if choice.startswith('s'):
            return "stand"
        print("Invalid move. Please type 'hit' or 'stand'.")