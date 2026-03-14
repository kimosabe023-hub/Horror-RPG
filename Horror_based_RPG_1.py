"""
Ultimate Haunted Mansion Horror – Expanded Nightmare Edition
Features: inventory system with weight, sanity hallucinations, status effects, companion, multi-step puzzles
"""

import random
import time
import json
import os
import threading
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

# ────────────────────────────────────────────────
# Config
# ────────────────────────────────────────────────

SAVE_FILE = "haunted_mansion_nightmare.json"
SLOW_DELAY = 0.028
PUZZLE_TIMEOUT = 45
MAX_INVENTORY_WEIGHT = 18

SANITY_TIERS = {
    100: "clear",
    70:  "uneasy",
    50:  "unsettled",
    35:  "distorted",
    20:  "fractured",
    10:  "shattered",
     0:  "broken"
}

# ────────────────────────────────────────────────
# Utilities
# ────────────────────────────────────────────────

def slow(s: str, delay: float = SLOW_DELAY):
    for c in s:
        print(c, end='', flush=True)
        time.sleep(delay)
    print()


def timed_input(prompt: str, timeout: int = PUZZLE_TIMEOUT, default="") -> str:
    res = [default]
    def target():
        try: res[0] = input(prompt).strip()
        except: pass
    t = threading.Thread(target=target, daemon=True)
    t.start()
    t.join(timeout)
    if t.is_alive():
        print(f"\nTime's up → {default}")
    return res[0]


def cls():
    os.system('cls' if os.name == 'nt' else 'clear')


def pause():
    input("\n[ ⏎ ] ")


# ────────────────────────────────────────────────
# Data
# ────────────────────────────────────────────────

@dataclass
class Item:
    name: str
    desc: str
    weight: int = 1
    usable: bool = False
    combat_bonus: int = 0
    heal_hp: int = 0
    heal_sanity: int = 0
    cures: List[str] = None           # e.g. ["poisoned", "bleeding"]
    examine_text: str = ""


@dataclass
class Status:
    name: str
    turns_left: int
    hp_per_turn: int = 0
    sanity_per_turn: int = 0
    desc: str = ""


@dataclass
class PuzzleStep:
    q: str
    a: str
    hint: str = ""
    success: str = "Correct."
    fail: str = "Wrong."


@dataclass
class Puzzle:
    name: str
    steps: List[PuzzleStep]
    reward: str           # item name
    flag: str


@dataclass
class NPC:
    name: str
    desc: str
    greet: str
    recruit_line: str
    combat_line: str
    combat_dmg: int = 0
    recruited: bool = False


@dataclass
class Enemy:
    name: str
    hp: int
    max_hp: int
    sanity_hit: int
    desc: str
    atk_desc: str
    dmg_low: int = 7
    dmg_high: int = 24


@dataclass
class Room:
    key: str
    title: str
    base_desc: str
    exits: List[str]
    items: List[str]                # item names
    puzzle: Optional[Puzzle] = None
    npc: Optional[NPC] = None
    enter_event_chance: float = 0.0


# ────────────────────────────────────────────────
# Content
# ────────────────────────────────────────────────

ITEMS = {
    "flashlight": Item("flashlight", "Old but bright", weight=2, examine_text="The beam flickers sometimes... like it's afraid."),
    "iron_key":   Item("iron key", "Heavy, cold, engraved with thorns", weight=2),
    "bandages":   Item("bandages", "Stained but usable", usable=True, heal_hp=20, cures=["bleeding"], weight=1),
    "antidote":   Item("antidote vial", "Green liquid swirls inside", usable=True, cures=["poisoned"], weight=1),
    "silver_knife": Item("silver knife", "Etched with protective runes", weight=2, usable=True, combat_bonus=18, examine_text="Feels warm when near spirits."),
    "old_locket": Item("old locket", "Contains a faded photograph", usable=True, heal_sanity=30, weight=1,
                       examine_text="Inside is a picture of a smiling child… the eyes follow you."),
    "broken_mirror": Item("broken mirror shard", "Reflects things that aren't there", weight=2, combat_bonus=15,
                          examine_text="Sometimes you see someone standing behind you in the reflection."),
}

PUZZLES = {
    "clock_riddle": Puzzle(
        "clock_riddle",
        [
            PuzzleStep("What has a face and two hands but no arms or legs?", "clock"),
            PuzzleStep("Now tell me what runs but never walks, has a bed but never sleeps.", "river"),
            PuzzleStep("One last word — what is the sound of the house when it hungers?", "silence")
        ],
        "old_locket",
        "clock_solved"
    ),
}

NPCS = {
    "elena": NPC(
        "Elena",
        "Translucent maid, eyes full of sorrow",
        "…you see me? Truly see me?",
        "If you can end this nightmare… I will walk with you until the end.",
        "I'll keep it busy — strike true!",
        combat_dmg=11
    )
}

ENEMIES = {
    "wraith": Enemy("Grieving Wraith", 60, 60, 15, "Woman in torn veil floats silently.", "Her wail tears at your mind."),
    "crawling": Enemy("Crawling Remains", 75, 75, 9, "Twisted servant drags itself forward.", "Fingernails scrape stone."),
}

BOSSES = [
    Enemy("Lady Seraphine", 200, 200, 26, "Black wedding dress drips ichor.", "Her grief drowns reality."),
    Enemy("The House Avatar", 340, 340, 38, "Walls pulse like flesh. Eyes open.", "The mansion rejects you."),
]

ROOMS = {
    "vestibule": Room(
        "vestibule", "Vestibule of Decay",
        "Cracked marble. Chandelier sways with no wind.",
        ["great_hall", "west_wing"],
        ["flashlight", "iron_key"]
    ),
    "great_hall": Room(
        "great_hall", "Grand Hall",
        "Portraits stare. The carpet smells of old blood.",
        ["vestibule", "library", "servants", "dining"],
        [],
        enter_event_chance=0.30
    ),
    "library": Room(
        "library", "Moldering Library",
        "Books breathe when you're not looking.",
        ["great_hall", "study"],
        ["bandages"],
        PUZZLES["clock_riddle"]
    ),
    "study": Room(
        "study", "Hidden Study",
        "One candle never dies. Papers written in something red.",
        ["library"],
        ["antidote", "silver_knife"]
    ),
    "servants": Room(
        "servants", "Servants' Wing",
        "Beds still unmade. One figure sits in the dark.",
        ["great_hall", "kitchen"],
        [],
        npc=NPCS["elena"]
    ),
    "kitchen": Room(
        "kitchen", "Butcher's Kitchen",
        "Meat hooks sway. Something drips from the ceiling.",
        ["servants", "cellar"],
        ["broken_mirror"]
    ),
    "cellar": Room(
        "cellar", "Deep Cellar",
        "Chains. Damp. Breathing in the dark.",
        ["kitchen"],
        [],
        enter_event_chance=0.45
    ),
}

# ────────────────────────────────────────────────
# Player
# ────────────────────────────────────────────────

class Player:
    def __init__(self, name: str):
        self.name = name
        self.hp = 100
        self.max_hp = 100
        self.sanity = 100
        self.max_sanity = 100
        self.inventory: List[str] = []
        self.weight_carried = 0
        self.location = "vestibule"
        self.flags = set()
        self.statuses: List[Status] = []
        self.companion: Optional[NPC] = None
        self.alive = True
        self.ending = None

    def inventory_weight(self) -> int:
        return sum(ITEMS[it].weight for it in self.inventory)

    def can_take(self, item_name: str) -> bool:
        item = ITEMS[item_name]
        return self.inventory_weight() + item.weight <= MAX_INVENTORY_WEIGHT

    def add_item(self, name: str) -> bool:
        if name not in ITEMS:
            return False
        if not self.can_take(name):
            slow("It's too heavy... you can't carry more.")
            return False
        self.inventory.append(name)
        slow(f"You take the {ITEMS[name].name}.")
        return True

    def remove_item(self, name: str) -> bool:
        if name in self.inventory:
            self.inventory.remove(name)
            return True
        return False

    def use_item(self, name: str):
        if name not in self.inventory:
            slow("You don't have that.")
            return
        item = ITEMS[name]

        if item.usable:
            if item.heal_hp:
                old = self.hp
                self.hp = min(self.max_hp, self.hp + item.heal_hp)
                slow(f"HP restored: +{self.hp - old}")
            if item.heal_sanity:
                old = self.sanity
                self.sanity = min(self.max_sanity, self.sanity + item.heal_sanity)
                slow(f"Sanity restored: +{self.sanity - old}")
            if item.cures:
                for s in item.cures:
                    self.statuses = [st for st in self.statuses if st.name.lower() != s.lower()]
                    slow(f"You are no longer {s}.")
            self.remove_item(name)
        else:
            slow("That item cannot be used right now.")

    def examine_item(self, name: str):
        if name in self.inventory and name in ITEMS:
            item = ITEMS[name]
            slow(f"\n{item.name.upper()}")
            slow(item.desc)
            if item.examine_text:
                slow("→ " + item.examine_text)
        else:
            slow("You don't have that.")

    def get_sanity_tier(self) -> str:
        for thresh, tier in sorted(SANITY_TIERS.items(), reverse=True):
            if self.sanity >= thresh:
                return tier
        return "broken"

    def hallucination(self):
        tier = self.get_sanity_tier()
        hallucinations = {
            "uneasy":    ["The wallpaper seems to pulse slowly…", "You thought you heard your name…"],
            "unsettled": ["Footsteps behind you… but you're alone.", "The portraits blink when you look away."],
            "distorted": ["The floor tilts… or is it your mind?", "Your shadow moves before you do."],
            "fractured": ["Someone is standing right behind you…", "The walls are breathing your name."],
            "shattered": ["You see yourself lying dead in the corner.", "The house whispers: you were never alive."],
            "broken":    ["Reality folds. You are the house now."],
        }
        msg = random.choice(hallucinations.get(tier, hallucinations["uneasy"]))
        slow("\n" + msg)
        if tier in ("fractured", "shattered", "broken"):
            self.sanity -= random.randint(2, 7)
            slow(f"Sanity slips further... ({self.sanity})")

    def tick(self):
        to_remove = []
        for s in self.statuses:
            if s.hp_per_turn:     self.hp     -= s.hp_per_turn
            if s.sanity_per_turn: self.sanity -= s.sanity_per_turn
            s.turns_left -= 1
            if s.turns_left <= 0:
                to_remove.append(s)
                slow(f"→ {s.name} wears off.")
        for r in to_remove:
            self.statuses.remove(r)

        # Hallucinations based on sanity
        if self.sanity <= 70:
            if random.random() < (100 - self.sanity) / 120:
                self.hallucination()

        if self.sanity <= 0:
            self.alive = False
            self.ending = "madness"


# ────────────────────────────────────────────────
# Game Logic
# ────────────────────────────────────────────────

def horror_event(p: Player, chance: float):
    if random.random() > chance: return
    roll = random.random()
    if roll < 0.30:
        p.sanity -= random.randint(5,12)
        slow("→ Something cold brushes your neck… sanity slips.")
    elif roll < 0.55:
        p.statuses.append(Status("Bleeding", 4, hp_per_turn=4, desc="Blood drips steadily."))
    elif roll < 0.80:
        p.statuses.append(Status("Poisoned", 5, hp_per_turn=5, sanity_per_turn=4, desc="Venom burns inside."))
    else:
        p.statuses.append(Status("Terrified", 3, sanity_per_turn=10, desc="You can barely breathe."))


def combat(p: Player, enemy: Enemy) -> bool:
    cls()
    slow(f"\n{enemy.name} emerges!\n{enemy.desc}\n")

    while enemy.hp > 0 and p.alive:
        p.tick()
        if not p.alive: break

        print(f"  HP {p.hp}/{p.max_hp}   Sanity {p.sanity}/{p.max_sanity}")
        if p.statuses:
            print("  Status: " + ", ".join(s.name for s in p.statuses))
        print("\n  [a]ttack   [i]tem   [f]lee" + ("   [c]ompanion" if p.companion else ""))
        act = input("  > ").strip().lower()

        if act in ("a", "attack"):
            base = random.randint(9, 22)
            bonus = sum(ITEMS[it].combat_bonus for it in p.inventory)
            dmg = base + bonus
            enemy.hp -= dmg
            slow(f"You strike for {dmg} damage.")

        elif act == "i":
            if not p.inventory:
                slow("Nothing useful.")
                continue
            slow("Inventory: " + ", ".join(p.inventory))
            which = input("Use which? > ").strip().lower()
            if which in p.inventory:
                p.use_item(which)
            else:
                slow("No such item.")

        elif act in ("f", "flee"):
            chance = 0.55
            if p.companion: chance += 0.20
            if random.random() < chance:
                slow("You escape!")
                return True
            slow("You can't get away!")

        elif act == "c" and p.companion:
            enemy.hp -= p.companion.combat_dmg
            slow(f"{p.companion.name}: {p.companion.combat_line} → {p.companion.combat_dmg} dmg")

        if enemy.hp > 0:
            dmg = random.randint(enemy.dmg_low, enemy.dmg_high)
            p.hp -= dmg
            p.sanity -= enemy.sanity_hit
            slow(f"{enemy.atk_desc} → -{dmg} HP   sanity-{enemy.sanity_hit}")

        if p.hp <= 0 or p.sanity <= 0:
            p.alive = False
            return False

    slow(f"\n{enemy.name} collapses / fades / dies.")
    return True


def describe_room(p: Player):
    room = ROOMS[p.location]
    tier = p.get_sanity_tier()

    distorted_desc = room.base_desc
    if tier in ("distorted", "fractured", "shattered", "broken"):
        add = random.choice([
            "…the corners bend inward…",
            "…everything is slightly too red…",
            "…you hear breathing behind the walls…"
        ])
        distorted_desc += add

    slow(f"\n════ {room.title.upper()} ════")
    slow(distorted_desc)

    if room.items:
        names = [ITEMS[it].name for it in room.items]
        slow(f"\nYou see: {', '.join(names)}")

    if room.npc and not room.npc.recruited:
        slow(f"\n→ {room.npc.desc}")

    print(f"\nExits: {', '.join(ROOMS[e].title for e in room.exits)}")


def try_recruit(p: Player, npc: NPC):
    if npc.recruited: return
    slow(f"\n{npc.name}: {npc.greet}")
    if input("  Try to gain her trust? [y/N] → ").lower().startswith('y'):
        slow(npc.recruit_line)
        npc.recruited = True
        p.companion = npc
        slow(f"{npc.name} now follows you… quietly.")
    else:
        slow("She lowers her gaze and fades slightly.")


def solve_puzzle(p: Player, puzzle: Puzzle):
    if puzzle.flag in p.flags: return

    slow(f"\n┌─ {puzzle.name.replace('_',' ').title()} ─┐")

    for i, step in enumerate(puzzle.steps, 1):
        slow(f" {i}. {step.q}")
        if step.hint and input("  Hint? [y/N] → ").lower().startswith('y'):
            slow(f"  → {step.hint}")

        ans = timed_input("  > ", PUZZLE_TIMEOUT, "").lower()
        if ans != step.a.lower():
            slow(step.fail)
            p.sanity -= 14
            p.flags.add(puzzle.flag)
            return
        slow(step.success)

    slow("\nPuzzle complete.")
    if puzzle.reward:
        p.add_item(puzzle.reward)
    p.flags.add(puzzle.flag)


def game_loop(p: Player):
    while p.alive and not p.ending:
        cls()
        describe_room(p)

        print(f"\nHP {p.hp} | Sanity {p.sanity} | Weight {p.inventory_weight()}/{MAX_INVENTORY_WEIGHT}")
        if p.statuses:
            print("Status: " + ", ".join(s.name for s in p.statuses))
        if p.companion:
            print(f"Companion: {p.companion.name}")

        room = ROOMS[p.location]

        # Enter event
        if random.random() < room.enter_event_chance:
            horror_event(p, 1.0)

        # Puzzle
        if room.puzzle and room.puzzle.flag not in p.flags:
            solve_puzzle(p, room.puzzle)

        # NPC
        if room.npc and not room.npc.recruited:
            try_recruit(p, room.npc)

        print("\n m = move   t = take   drop = drop   use = use")
        print(" inv = inventory   ex = examine   s = save   q = quit")
        cmd = input("\n> ").strip().lower()

        if cmd in ("m", "move"):
            print("\nWhere?")
            for i,e in enumerate(room.exits,1):
                print(f" {i}) {ROOMS[e].title}")
            choice = input("> ").strip()
            try: dest = room.exits[int(choice)-1]
            except: dest = choice
            if dest in room.exits:
                p.location = dest
                p.tick()
            else:
                slow("No such path.")

        elif cmd in ("t", "take"):
            if room.items:
                it = room.items.pop(0)
                if p.add_item(it):
                    pass
            else:
                slow("Nothing here.")

        elif cmd == "drop":
            if not p.inventory:
                slow("Nothing to drop.")
                continue
            slow("Inventory: " + ", ".join(p.inventory))
            which = input("Drop what? > ").strip().lower()
            if p.remove_item(which):
                slow(f"Dropped {which}.")
            else:
                slow("No such item.")

        elif cmd == "use":
            if not p.inventory:
                slow("Nothing to use.")
                continue
            slow("Inventory: " + ", ".join(p.inventory))
            which = input("Use what? > ").strip().lower()
            p.use_item(which)

        elif cmd == "ex" or cmd == "examine":
            which = input("Examine what? > ").strip().lower()
            p.examine_item(which)

        elif cmd == "inv":
            if not p.inventory:
                slow("Inventory empty.")
            else:
                slow("Carrying:")
                for it in p.inventory:
                    print(f" • {ITEMS[it].name}  ({ITEMS[it].weight} kg) — {ITEMS[it].desc}")
            pause()

        elif cmd in ("s", "save"):
            save_game(p)
            pause()

        elif cmd in ("q", "quit"):
            if input("Quit? [y/N] ").lower().startswith('y'):
                break

        # Ending conditions
        if p.sanity <= 0:
            p.ending = "madness"
        if p.hp <= 0:
            p.ending = "death"
        # You can add victory condition here (e.g. defeat final boss + escape flag)

    ending_screen(p)


def ending_screen(p: Player):
    cls()
    slow("\n" + "═"*70 + "\n")
    if p.ending == "madness":
        slow("  YOUR MIND SHATTERED")
        slow("  You are now part of the house. Forever.")
    elif p.ending == "death":
        slow("  YOUR BODY FAILED")
        slow("  Another portrait added to the collection.")
    else:
        slow("  YOU WALKED AWAY… FOR NOW")
        slow("  But the house remembers your name.")
    slow("\n" + "═"*70 + "\n")
    pause()


def save_game(p: Player):
    data = {
        "name": p.name,
        "hp": p.hp,
        "sanity": p.sanity,
        "location": p.location,
        "inventory": p.inventory,
        "flags": list(p.flags),
        "companion": p.companion.name if p.companion else None,
    }
    with open(SAVE_FILE, "w") as f:
        json.dump(data, f, indent=2)
    slow("Game saved.")


def load_game() -> Optional[Player]:
    if not os.path.exists(SAVE_FILE): return None
    try:
        with open(SAVE_FILE) as f:
            d = json.load(f)
        p = Player(d["name"])
        p.hp = d["hp"]
        p.sanity = d["sanity"]
        p.location = d["location"]
        p.inventory = d["inventory"]
        p.flags = set(d["flags"])
        if d.get("companion"):
            npc = NPCS.get(d["companion"])
            if npc:
                npc.recruited = True
                p.companion = npc
        return p
    except:
        return None


# ────────────────────────────────────────────────
# Entry
# ────────────────────────────────────────────────

def main():
    cls()
    slow("  ULTIMATE HAUNTED MANSION – NIGHTMARE EDITION")
    slow("  inventory • hallucinations • companion • dread\n")

    p = None
    if input("Load previous torment? [y/N] → ").lower().startswith('y'):
        p = load_game()
        if p:
            slow(f"The house remembers you, {p.name}…")

    if not p:
        name = input("Who dares enter? ").strip() or "Forgotten"
        p = Player(name)

    slow(f"\nWelcome back… {p.name}")
    slow("The doors are already closing behind you.")
    pause()
    game_loop(p)


if __name__ == "__main__":
    main()
