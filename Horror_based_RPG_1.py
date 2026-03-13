import random, time, json, os, threading

# -------------------------
# Helper Functions
# -------------------------
def slow_print(text, delay=0.03):
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()

def timed_input(prompt, timeout=10, default=""):
    user_input = [default]
    def get_input():
        user_input[0] = input(prompt)
    thread = threading.Thread(target=get_input)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        print(f"\nTime's up! Default choice: {default}")
    return user_input[0]

def clear_screen():
    os.system('cls' if os.name=='nt' else 'clear')

def pause():
    input("\nPress Enter to continue...")

# -------------------------
# Player Class
# -------------------------
class Player:
    def __init__(self, name):
        self.name=name
        self.health=100
        self.sanity=100
        self.stamina=100
        self.inventory=[]
        self.location='foyer'
        self.alive=True
        self.chapter=1
        self.flags={}
        self.cursed=False
        self.traps_triggered=0

    def show_stats(self):
        print(f"\n[{self.name}'s Stats] Health: {self.health}, Sanity: {self.sanity}, Stamina: {self.stamina}")
        print(f"Inventory: {', '.join(self.inventory) if self.inventory else 'Empty'}")

# -------------------------
# Rooms and Puzzles
# -------------------------
rooms = {
    'foyer': {'desc': "The mansion's foyer is dark. Chandelier sways, doors lead onward.", 'exits': ['hallway'], 'items': ['flashlight']},
    'hallway': {'desc': "Narrow hallway. Eyes of portraits follow you.", 'exits': ['library','kitchen','attic','chapel','foyer'], 'items': []},
    'library': {'desc': "Dusty books. Whispers echo.", 'exits': ['hallway','secret_room','attic_secret'], 'items': ['ancient tome'], 'puzzle': {'question': "I have keys but no locks, space but no room. What am I?", 'answer': "keyboard", 'reward': 'cursed amulet'}},
    'secret_room': {'desc': "Hidden room with arcane symbols.", 'exits': ['library'], 'items': [], 'puzzle': {'question': "Speak the word that ends all words...", 'answer': "end", 'reward': 'magic crystal'}},
    'attic_secret': {'desc': "Hidden attic space with forbidden books.", 'exits': ['attic'], 'items': ['forbidden tome'], 'puzzle': {'question': "Name the fear that stalks every mind...", 'answer': "darkness", 'reward': 'elder talisman'}},
    'kitchen': {'desc': "Rotting food. Broken knives litter floor.", 'exits': ['hallway','basement','dining_room'], 'items': ['knife']},
    'dining_room': {'desc': "Long dusty table. Silverware moves.", 'exits': ['kitchen','pantry'], 'items': ['candle']},
    'pantry': {'desc': "Shelves filled with spoiled food.", 'exits': ['dining_room'], 'items': []},
    'basement': {'desc': "Pitch black. Chains rattle. Something breathes.", 'exits': ['kitchen','hidden_lab','crypt'], 'items': ['key']},
    'hidden_lab': {'desc': "Broken vials, strange fluids, shadows twitch.", 'exits': ['basement','tower'], 'items': ['healing potion']},
    'attic': {'desc': "Cobwebs. Cold wind chills.", 'exits': ['hallway','tower'], 'items': ['ancient dagger']},
    'tower': {'desc': "Wind howls. Eyes follow you.", 'exits': ['attic','hidden_lab','observatory','balcony'], 'items': ['mysterious scroll']},
    'observatory': {'desc': "Broken telescope points to a blood-red moon.", 'exits': ['tower'], 'items': ['magic crystal']},
    'chapel': {'desc': "Dusty chapel. Shadows twist.", 'exits': ['hallway'], 'items': ['holy water']},
    'crypt': {'desc': "Cold crypt. Coffins rattle.", 'exits': ['basement'], 'items': ['ancient key']},
    'balcony': {'desc': "High balcony. Wind dizzying.", 'exits': ['tower'], 'items': []},
    'garden': {'desc': "Overgrown garden. Statues seem alive.", 'exits': ['foyer'], 'items': []},
    'attic_secret2': {'desc': "A forbidden chamber with strange glowing symbols.", 'exits': ['attic'], 'items': ['curse scroll'], 'puzzle': {'question': "I bind the living to shadows, who am I?", 'answer': 'curse', 'reward': 'haunted ring'}},
    'secret_hall': {'desc': "A dark secret hallway, walls drip black ichor.", 'exits': ['library','tower'], 'items': []},
    'hidden_chamber': {'desc': "The mansion’s most forbidden chamber.", 'exits': ['secret_room'], 'items': ['elder staff']},
}

# -------------------------
# Enemy and Boss Classes
# -------------------------
class Enemy:
    def __init__(self,name,health,sanity_damage,description):
        self.name=name
        self.health=health
        self.sanity_damage=sanity_damage
        self.description=description
    def attack(self,player):
        slow_print(f"\n{self.name} attacks!")
        dmg=random.randint(5,25)
        player.health-=dmg
        player.sanity-=self.sanity_damage
        slow_print(f"You lose {dmg} health and {self.sanity_damage} sanity! Health: {player.health}, Sanity: {player.sanity}")

ghosts=[Enemy("Restless Spirit",30,10,"A pale figure floats silently."),
        Enemy("Wailing Specter",40,15,"A ghastly scream pierces your mind."),
        Enemy("Creeping Shadow",25,5,"Something unseen brushes past your skin."),
        Enemy("Dread Phantom",35,15,"A horrific figure lunges from the shadows.")]

bosses=[Enemy("Esai The Tormented",120,20,"A massive shadow towers with glowing eyes."),
        Enemy("NovNod The Mad Alchemist",150,15,"A crazed scientist lunges with a broken vial."),
        Enemy("Marcou's Esquire The Third",200,25,"An armored figure with flaming eyes blocks your path."),
        Enemy("Raymond Omega",250,30,"An ancient evil with reality-bending powers.")]

# -------------------------
# Save/Load System
# -------------------------
SAVE_FILE="ultimate_horror_save.json"
def save_game(player):
    data={'name':player.name,'health':player.health,'sanity':player.sanity,'stamina':player.stamina,
          'inventory':player.inventory,'location':player.location,'chapter':player.chapter,'flags':player.flags,'cursed':player.cursed,'traps_triggered':player.traps_triggered}
    with open(SAVE_FILE,'w') as f:
        json.dump(data,f)
    slow_print("Game saved!")

def load_game():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE) as f:
            data=json.load(f)
            p=Player(data['name'])
            p.health=data['health']
            p.sanity=data['sanity']
            p.stamina=data['stamina']
            p.inventory=data['inventory']
            p.location=data['location']
            p.chapter=data.get('chapter',1)
            p.flags=data.get('flags',{})
            p.cursed=data.get('cursed',False)
            p.traps_triggered=data.get('traps_triggered',0)
            return p
    return None

# -------------------------
# Combat System
# -------------------------
def combat(player,enemy):
    slow_print(f"\nYou encounter {enemy.name}! {enemy.description}")
    while enemy.health>0 and player.alive:
        slow_print("\nOptions: [attack] [flee] [use item]")
        choice=input("> ").lower()
        if choice=="attack":
            dmg=random.randint(10,30)
            enemy.health-=dmg
            slow_print(f"You attack {enemy.name} for {dmg} damage!")
        elif choice=="flee":
            if random.random()>0.5:
                slow_print("You escape!")
                return
            else:
                slow_print("Failed to escape!")
        elif choice=="use item":
            if 'knife' in player.inventory:
                slow_print("You slash with your knife!")
                enemy.health-=random.randint(15,35)
            elif 'healing potion' in player.inventory:
                slow_print("You drink a healing potion!")
                player.health+=random.randint(20,50)
                player.inventory.remove('healing potion')
            elif 'holy water' in player.inventory:
                slow_print("You splash holy water!")
                enemy.health-=random.randint(20,40)
            else:
                slow_print("Nothing useful!")
        else:
            slow_print("Invalid choice!")
        if enemy.health>0:
            enemy.attack(player)
        if player.health<=0 or player.sanity<=0:
            player.alive=False
            slow_print("You succumbed to wounds or insanity...")
            return
    slow_print(f"You defeated {enemy.name}!")

# -------------------------
# Random Horror Events & Traps
# -------------------------
def random_event(player):
    chance=random.random()
    if chance<0.2:
        combat(player,random.choice(ghosts))
    elif 0.2<=chance<0.4:
        slow_print("\nLights flicker. Footsteps echo...")
        player.sanity-=5
    elif 0.4<=chance<0.55:
        slow_print("\nYou find a mysterious potion.")
        player.inventory.append('healing potion')
    elif 0.55<=chance<0.7:
        slow_print("\nCold wind chills you. Sanity drops slightly.")
        player.sanity-=5
    elif 0.7<=chance<0.85:
        slow_print("\nA hidden trap triggers!")
        dmg=random.randint(10,25)
        player.health-=dmg
        player.traps_triggered+=1
        slow_print(f"You take {dmg} damage from the trap! Health: {player.health}")
    else:
        slow_print("\nAll is quiet... for now.")

# -------------------------
# Puzzle & Chapter System
# -------------------------
def check_chapter_progress(player):
    if player.chapter==1 and 'key' in player.inventory and not player.flags.get('chapter1_boss'):
        slow_print("\nThe key vibrates. A shadow approaches...")
        player.flags['chapter1_boss']=True
        player.chapter=2
        slow_print("\n--- Chapter 2: The Haunting Deepens ---")
        combat(player,random.choice(bosses))
    if player.chapter==2 and 'cursed amulet' in player.inventory and not player.flags.get('chapter2_boss'):
        slow_print("\nThe cursed amulet screams. Something ancient awakens...")
        player.flags['chapter2_boss']=True
        player.chapter=3
        slow_print("\n--- Chapter 3: Confront the Haunted ---")
        combat(player,random.choice(bosses))
    if player.chapter==3 and 'elder talisman' in player.inventory and not player.flags.get('final_boss'):
        slow_print("\nA terrifying presence fills the mansion...")
        player.flags['final_boss']=True
        slow_print("\n--- Final Chapter: The Elder Horror ---")
        combat(player,Enemy("Elder Horror",300,35,"The mansion itself warps reality!"))

def solve_puzzle(player, room):
    puzzle=rooms[room].get('puzzle')
    if puzzle and not player.flags.get(f"puzzle_{room}"):
        answer=timed_input(f"\nPuzzle: {puzzle['question']}\nYour answer (30 sec): ",30,"")
        if answer.strip().lower()==puzzle['answer']:
            slow_print("Correct! You receive: "+puzzle['reward'])
            player.inventory.append(puzzle['reward'])
            player.flags[f"puzzle_{room}"]=True
        else:
            slow_print("Incorrect! Sanity drops.")
            player.sanity-=10
            player.flags[f"puzzle_{room}"]=True

# -------------------------
# Dynamic Room Description
# -------------------------
def describe_room(player):
    room=rooms[player.location]
    desc=room['desc']
    if player.sanity<50:
        desc+="\nShadows twist unnaturally, and whispers taunt you."
    if player.sanity<20:
        desc+="\nReality shatters. The mansion is alive and malevolent."
    slow_print(desc)

# -------------------------
# Main Game Loop
# -------------------------
def game_loop(player):
    while player.alive:
        clear_screen()
        slow_print(f"\n--- You are in {player.location} ---")
        describe_room(player)
        player.show_stats()
        if rooms[player.location]['items']:
            slow_print(f"You see: {', '.join(rooms[player.location]['items'])}")
        slow_print(f"Exits: {', '.join(rooms[player.location]['exits'])}")
        solve_puzzle(player,player.location)
        slow_print("\nWhat will you do? [move] [take] [inventory] [save] [quit]")
        action=input("> ").lower()
        if action=="move":
            dest=input("Where? ").lower()
            if dest in rooms[player.location]['exits']:
                player.location=dest
                random_event(player)
                check_chapter_progress(player)
            else:
                slow_print("Can't go that way.")
        elif action=="take":
            if rooms[player.location]['items']:
                item=rooms[player.location]['items'].pop(0)
                player.inventory.append(item)
                slow_print(f"You picked up {item}.")
            else:
                slow_print("Nothing to take here.")
        elif action=="inventory":
            player.show_stats()
            pause()
        elif action=="save":
            save_game(player)
        elif action=="quit":
            slow_print("Exiting game...")
            break
        else:
            slow_print("Unknown action.")
        if player.sanity<=0:
            slow_print("\nYour mind shatters. You cannot continue...")
            player.alive=False
    slow_print("\nGame Over.")
    if player.sanity<=0 and player.cursed:
        slow_print("You became fully cursed and trapped forever in the mansion...")
    elif player.sanity<=0:
        slow_print("You went insane, lost in shadows forever...")
    elif player.alive:
        slow_print("You survived... but the mansion's curse lingers.")

# -------------------------
# Main
# -------------------------
def main():
    clear_screen()
    slow_print("Welcome to the Ultimate Haunted Mansion Horror RPG - Ultimate Edition!")
    choice=input("Load previous game? [y/n] ").lower()
    if choice=='y':
        player=load_game()
        if not player:
            slow_print("No saved game found.")
            name=input("Enter your name: ")
            player=Player(name)
    else:
        name=input("Enter your name: ")
        player=Player(name)
    slow_print("\nSurvive the mansion, solve puzzles, fight bosses, keep sanity, uncover secrets...")
    pause()
    game_loop(player)

if __name__=="__main__":
    main()