def ask_rounds():
    r = int(input("how many rounds? "))
    return max(0, min(255, r))

def ask_name():
    s = input("team name: ").strip()
    if s == "":
        s = "player"
    return s

def ask_hit_or_stand():
    while True:
        s = input("hit or stand? ").strip().lower()
        if s.startswith("h"):
            return "hit"
        if s.startswith("s"):
            return "stand"