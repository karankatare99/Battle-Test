import json
import math
import random
import string
import sys
from datetime import datetime

# Load Pokemon and move data with error handling
try:
    with open("kanto_data.json", "r") as f:
        kanto_data = json.load(f)
    print("✅ Loaded Kanto Pokemon data successfully!")
except FileNotFoundError:
    print("❌ Error: kanto_data.json file not found!")
    print("Please ensure kanto_data.json is in the same directory as the bot.")
    sys.exit(1)
except json.JSONDecodeError as e:
    print(f"❌ Error: Invalid JSON in kanto_data.json: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error loading kanto_data.json: {e}")
    sys.exit(1)

try:
    with open("moves.json", "r") as f:
        moves_data = json.load(f)
    print("✅ Loaded moves data successfully!")
except FileNotFoundError:
    print("❌ Error: moves.json file not found!")
    print("Please ensure moves.json is in the same directory as the bot.")
    sys.exit(1)
except json.JSONDecodeError as e:
    print(f"❌ Error: Invalid JSON in moves.json: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error loading moves.json: {e}")
    sys.exit(1)

# Nature effects chart
nature_chart = {
    "Adamant": {"atk": 1.1, "spa": 0.9},
    "Lonely": {"atk": 1.1, "def": 0.9},
    "Brave": {"atk": 1.1, "spe": 0.9},
    "Naughty": {"atk": 1.1, "spd": 0.9},
    "Bold": {"def": 1.1, "atk": 0.9},
    "Impish": {"def": 1.1, "spa": 0.9},
    "Relaxed": {"def": 1.1, "spe": 0.9},
    "Lax": {"def": 1.1, "spd": 0.9},
    "Modest": {"spa": 1.1, "atk": 0.9},
    "Mild": {"spa": 1.1, "def": 0.9},
    "Quiet": {"spa": 1.1, "spe": 0.9},
    "Rash": {"spa": 1.1, "spd": 0.9},
    "Calm": {"spd": 1.1, "atk": 0.9},
    "Gentle": {"spd": 1.1, "def": 0.9},
    "Sassy": {"spd": 1.1, "spe": 0.9},
    "Careful": {"spd": 1.1, "spa": 0.9},
    "Timid": {"spe": 1.1, "atk": 0.9},
    "Hasty": {"spe": 1.1, "def": 0.9},
    "Jolly": {"spe": 1.1, "spa": 0.9},
    "Naive": {"spe": 1.1, "spd": 0.9},
    # Neutral natures
    "Hardy": {}, "Docile": {}, "Serious": {}, "Bashful": {}, "Quirky": {}
}

# Type effectiveness chart
type_chart = {
    "normal": {"normal": 1, "fire": 1, "water": 1, "electric": 1, "grass": 1, "ice": 1, "fighting": 1, "poison": 1, "ground": 1, "flying": 1, "psychic": 1, "bug": 1, "rock": 0.5, "ghost": 0, "dragon": 1, "dark": 1, "steel": 0.5, "fairy": 1},
    "fire": {"normal": 1, "fire": 0.5, "water": 0.5, "electric": 1, "grass": 2, "ice": 2, "fighting": 1, "poison": 1, "ground": 1, "flying": 1, "psychic": 1, "bug": 2, "rock": 0.5, "ghost": 1, "dragon": 0.5, "dark": 1, "steel": 2, "fairy": 1},
    "water": {"normal": 1, "fire": 2, "water": 0.5, "electric": 1, "grass": 0.5, "ice": 1, "fighting": 1, "poison": 1, "ground": 2, "flying": 1, "psychic": 1, "bug": 1, "rock": 2, "ghost": 1, "dragon": 0.5, "dark": 1, "steel": 1, "fairy": 1},
    "electric": {"normal": 1, "fire": 1, "water": 2, "electric": 0.5, "grass": 0.5, "ice": 1, "fighting": 1, "poison": 1, "ground": 0, "flying": 2, "psychic": 1, "bug": 1, "rock": 1, "ghost": 1, "dragon": 0.5, "dark": 1, "steel": 1, "fairy": 1},
    "grass": {"normal": 1, "fire": 0.5, "water": 2, "electric": 1, "grass": 0.5, "ice": 1, "fighting": 1, "poison": 0.5, "ground": 2, "flying": 0.5, "psychic": 1, "bug": 0.5, "rock": 2, "ghost": 1, "dragon": 0.5, "dark": 1, "steel": 0.5, "fairy": 1},
    "ice": {"normal": 1, "fire": 0.5, "water": 0.5, "electric": 1, "grass": 2, "ice": 0.5, "fighting": 1, "poison": 1, "ground": 2, "flying": 2, "psychic": 1, "bug": 1, "rock": 1, "ghost": 1, "dragon": 2, "dark": 1, "steel": 0.5, "fairy": 1},
    "fighting": {"normal": 2, "fire": 1, "water": 1, "electric": 1, "grass": 1, "ice": 2, "fighting": 1, "poison": 0.5, "ground": 1, "flying": 0.5, "psychic": 0.5, "bug": 0.5, "rock": 2, "ghost": 0, "dragon": 1, "dark": 2, "steel": 2, "fairy": 0.5},
    "poison": {"normal": 1, "fire": 1, "water": 1, "electric": 1, "grass": 2, "ice": 1, "fighting": 1, "poison": 0.5, "ground": 0.5, "flying": 1, "psychic": 1, "bug": 1, "rock": 0.5, "ghost": 0.5, "dragon": 1, "dark": 1, "steel": 0, "fairy": 2},
    "ground": {"normal": 1, "fire": 2, "water": 1, "electric": 2, "grass": 0.5, "ice": 1, "fighting": 1, "poison": 2, "ground": 1, "flying": 0, "psychic": 1, "bug": 0.5, "rock": 2, "ghost": 1, "dragon": 1, "dark": 1, "steel": 2, "fairy": 1},
    "flying": {"normal": 1, "fire": 1, "water": 1, "electric": 0.5, "grass": 2, "ice": 1, "fighting": 2, "poison": 1, "ground": 1, "flying": 1, "psychic": 1, "bug": 2, "rock": 0.5, "ghost": 1, "dragon": 1, "dark": 1, "steel": 0.5, "fairy": 1},
    "psychic": {"normal": 1, "fire": 1, "water": 1, "electric": 1, "grass": 1, "ice": 1, "fighting": 2, "poison": 2, "ground": 1, "flying": 1, "psychic": 0.5, "bug": 1, "rock": 1, "ghost": 1, "dragon": 1, "dark": 0, "steel": 0.5, "fairy": 1},
    "bug": {"normal": 1, "fire": 0.5, "water": 1, "electric": 1, "grass": 2, "ice": 1, "fighting": 0.5, "poison": 0.5, "ground": 1, "flying": 0.5, "psychic": 2, "bug": 1, "rock": 1, "ghost": 0.5, "dragon": 1, "dark": 2, "steel": 0.5, "fairy": 0.5},
    "rock": {"normal": 1, "fire": 2, "water": 1, "electric": 1, "grass": 1, "ice": 2, "fighting": 0.5, "poison": 1, "ground": 0.5, "flying": 2, "psychic": 1, "bug": 2, "rock": 1, "ghost": 1, "dragon": 1, "dark": 1, "steel": 0.5, "fairy": 1},
    "ghost": {"normal": 0, "fire": 1, "water": 1, "electric": 1, "grass": 1, "ice": 1, "fighting": 1, "poison": 1, "ground": 1, "flying": 1, "psychic": 2, "bug": 1, "rock": 1, "ghost": 2, "dragon": 1, "dark": 0.5, "steel": 1, "fairy": 1},
    "dragon": {"normal": 1, "fire": 1, "water": 1, "electric": 1, "grass": 1, "ice": 1, "fighting": 1, "poison": 1, "ground": 1, "flying": 1, "psychic": 1, "bug": 1, "rock": 1, "ghost": 1, "dragon": 2, "dark": 1, "steel": 0.5, "fairy": 0},
    "dark": {"normal": 1, "fire": 1, "water": 1, "electric": 1, "grass": 1, "ice": 1, "fighting": 0.5, "poison": 1, "ground": 1, "flying": 1, "psychic": 2, "bug": 1, "rock": 1, "ghost": 2, "dragon": 1, "dark": 0.5, "steel": 1, "fairy": 0.5},
    "steel": {"normal": 1, "fire": 0.5, "water": 0.5, "electric": 0.5, "grass": 1, "ice": 2, "fighting": 1, "poison": 1, "ground": 1, "flying": 1, "psychic": 1, "bug": 1, "rock": 2, "ghost": 1, "dragon": 1, "dark": 1, "steel": 0.5, "fairy": 2},
    "fairy": {"normal": 1, "fire": 0.5, "water": 1, "electric": 1, "grass": 1, "ice": 1, "fighting": 2, "poison": 0.5, "ground": 1, "flying": 1, "psychic": 1, "bug": 1, "rock": 1, "ghost": 1, "dragon": 2, "dark": 2, "steel": 0.5, "fairy": 1}
}

def generate_pokemon_id():
    """Generate unique Pokemon ID"""
    date_part = datetime.utcnow().strftime("%y%m%d")
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"PKM-{date_part}-{random_part}"

def parse_ev_line(ev_line):
    """Parse EV line from Showdown format - FIXED VERSION"""
    evs = {s: 0 for s in ["hp", "atk", "def", "spa", "spd", "spe"]}
    
    if not ev_line:
        return evs
    
    # Split by " / " (space-slash-space) which is the standard Showdown format
    parts = ev_line.split(" / ")
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # Split by space to separate value and stat name
        tokens = part.split()
        if len(tokens) >= 2:
            try:
                value = int(tokens[0])  # First part is the number
                stat_name = tokens[1].lower()  # Second part is stat name
                
                # Map stat names to our internal format
                stat_map = {
                    "hp": "hp",
                    "atk": "atk", "attack": "atk",
                    "def": "def", "defense": "def",
                    "spa": "spa", "spatk": "spa", "sp.atk": "spa", "sp. atk": "spa",
                    "spd": "spd", "spdef": "spd", "sp.def": "spd", "sp. def": "spd",
                    "spe": "spe", "speed": "spe", "spd": "spe"  # Note: Showdown uses "Spe" for speed
                }
                
                if stat_name in stat_map:
                    evs[stat_map[stat_name]] = min(value, 252)  # Cap at 252
                    print(f"Parsed EV: {stat_name} -> {stat_map[stat_name]} = {value}")
                else:
                    print(f"Unknown EV stat: {stat_name}")
                    
            except ValueError:
                print(f"Could not parse EV value: {part}")
                continue
    
    return evs

def parse_iv_line(iv_line):
    """Parse IV line from Showdown format - FIXED VERSION"""
    ivs = {s: 31 for s in ["hp", "atk", "def", "spa", "spd", "spe"]}
    
    if not iv_line:
        return ivs
    
    # Split by " / " (space-slash-space)
    parts = iv_line.split(" / ")
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # Split by space to separate value and stat name
        tokens = part.split()
        if len(tokens) >= 2:
            try:
                value = int(tokens[0])  # First part is the number
                stat_name = tokens[1].lower()  # Second part is stat name
                
                # Map stat names to our internal format
                stat_map = {
                    "hp": "hp",
                    "atk": "atk", "attack": "atk",
                    "def": "def", "defense": "def",
                    "spa": "spa", "spatk": "spa", "sp.atk": "spa", "sp. atk": "spa",
                    "spd": "spd", "spdef": "spd", "sp.def": "spd", "sp. def": "spd",
                    "spe": "spe", "speed": "spe"
                }
                
                if stat_name in stat_map:
                    ivs[stat_map[stat_name]] = max(0, min(value, 31))  # Cap between 0-31
                    print(f"Parsed IV: {stat_name} -> {stat_map[stat_name]} = {value}")
                else:
                    print(f"Unknown IV stat: {stat_name}")
                    
            except ValueError:
                print(f"Could not parse IV value: {part}")
                continue
    
    return ivs

def calculate_stat(base, iv, ev, level, nature, stat):
    """Calculate final Pokemon stat"""
    if stat == "hp":
        if base == 1:  # Shedinja case
            return 1
        return math.floor(((2 * base + iv + ev/4) * level / 100) + level + 10)
    else:
        stat_val = math.floor(((2 * base + iv + ev/4) * level / 100) + 5)
        
        # Apply nature modifier
        if nature in nature_chart and stat in nature_chart[nature]:
            stat_val = math.floor(stat_val * nature_chart[nature][stat])
        
        return stat_val

def parse_showdown_set(text):
    """Parse Pokemon from Showdown format - FIXED VERSION"""
    lines = text.strip().split('\n')
    pokemon = {}
    
    # Initialize default stats
    evs = {s: 0 for s in ["hp", "atk", "def", "spa", "spd", "spe"]}
    ivs = {s: 31 for s in ["hp", "atk", "def", "spa", "spd", "spe"]}
    
    # Parse first line (name, gender, item)
    first_line = lines[0]
    if "(M)" in first_line:
        gender = "Male"
        first_line = first_line.replace("(M)", "").strip()
    elif "(F)" in first_line:
        gender = "Female"
        first_line = first_line.replace("(F)", "").strip()
    else:
        gender = random.choice(["Male", "Female"])
    
    if "@" in first_line:
        name_part, item = first_line.split("@")
        pokemon["name"] = name_part.strip()
        pokemon["item"] = item.strip()
    else:
        pokemon["name"] = first_line.strip()
        pokemon["item"] = None
    
    # Set defaults
    pokemon["gender"] = gender
    pokemon["level"] = 100
    pokemon["nature"] = "Hardy"
    pokemon["shiny"] = False
    pokemon["moves"] = []
    pokemon["iv_stats"] = {}
    pokemon["ev_stats"] = {}
    pokemon["stats"] = {}
    
    # Parse remaining lines
    for line in lines[1:]:
        line = line.strip()
        if line.startswith("Ability:"):
            pokemon["ability"] = line.replace("Ability:", "").strip()
        elif line.startswith("Shiny:") or line == "Shiny: Yes":
            pokemon["shiny"] = True
        elif line.startswith("Tera Type:"):
            pokemon["tera_type"] = line.replace("Tera Type:", "").strip()
        elif line.startswith("Level:"):
            try:
                pokemon["level"] = int(line.replace("Level:", "").strip())
            except:
                pokemon["level"] = 100
        elif "Nature" in line:
            pokemon["nature"] = line.replace("Nature", "").strip()
        elif line.startswith("EVs:"):
            ev_line = line.replace("EVs:", "").strip()
            evs = parse_ev_line(ev_line)
            print(f"Parsed EVs: {evs}")
        elif line.startswith("IVs:"):
            iv_line = line.replace("IVs:", "").strip()
            ivs = parse_iv_line(iv_line)
            print(f"Parsed IVs: {ivs}")
        elif line.startswith("- "):
            move_name = line.replace("- ", "").strip()
            # Limit to 4 moves maximum (Pokemon rule)
            if len(pokemon["moves"]) < 4:
                pokemon["moves"].append(move_name)
                print(f"Added move {len(pokemon['moves'])}: {move_name}")
            else:
                print(f"⚠️ Skipped move '{move_name}' - Pokemon already has 4 moves (maximum allowed)")
    
    # Store EVs and IVs
    for stat in ["hp", "atk", "def", "spa", "spd", "spe"]:
        pokemon["ev_stats"][f"ev_{stat}"] = evs[stat]
        pokemon["iv_stats"][f"iv_{stat}"] = ivs[stat]
        pokemon[f"ev_{stat}"] = evs[stat]
        pokemon[f"iv_{stat}"] = ivs[stat]
    
    # Calculate final stats
    add_final_stats(pokemon)
    pokemon["pokemon_id"] = generate_pokemon_id()
    
    return pokemon

def add_final_stats(pokemon):
    """Calculate and add final stats to Pokemon"""
    name = pokemon["name"]
    level = pokemon["level"]
    nature = pokemon["nature"]
    
    if name not in kanto_data:
        print(f"Warning: {name} not found in kanto_data")
        return pokemon
    
    # Access the Base_Stats object directly (correct JSON structure)
    pokemon_data = kanto_data[name]
    
    if "Base_Stats" not in pokemon_data:
        print(f"Warning: Base_Stats not found for {name}")
        return pokemon
    
    base_stats = pokemon_data["Base_Stats"]
    
    # Extract individual base stats
    hp = base_stats.get("Hp", 50)
    atk = base_stats.get("Attack", 50)
    defense = base_stats.get("Defense", 50)
    spa = base_stats.get("Sp.Attack", 50)
    spd = base_stats.get("Sp.Defense", 50)
    spe = base_stats.get("Speed", 50)
    
    final_stats = {}
    final_stats["hp"] = calculate_stat(hp, pokemon["iv_stats"]["iv_hp"], pokemon["ev_stats"]["ev_hp"], level, nature, "hp")
    final_stats["atk"] = calculate_stat(atk, pokemon["iv_stats"]["iv_atk"], pokemon["ev_stats"]["ev_atk"], level, nature, "atk")
    final_stats["def"] = calculate_stat(defense, pokemon["iv_stats"]["iv_def"], pokemon["ev_stats"]["ev_def"], level, nature, "def")
    final_stats["spa"] = calculate_stat(spa, pokemon["iv_stats"]["iv_spa"], pokemon["ev_stats"]["ev_spa"], level, nature, "spa")
    final_stats["spd"] = calculate_stat(spd, pokemon["iv_stats"]["iv_spd"], pokemon["ev_stats"]["ev_spd"], level, nature, "spd")
    final_stats["spe"] = calculate_stat(spe, pokemon["iv_stats"]["iv_spe"], pokemon["ev_stats"]["ev_spe"], level, nature, "spe")
    
    pokemon["stats"].update(final_stats)
    
    # Also store stats directly for easy access
    for stat, value in final_stats.items():
        pokemon[f"final_{stat}"] = value
    
    print(f"✅ Final stats for {name}: HP:{hp}→{final_stats['hp']} ATK:{atk}→{final_stats['atk']} DEF:{defense}→{final_stats['def']} SPA:{spa}→{final_stats['spa']} SPD:{spd}→{final_stats['spd']} SPE:{spe}→{final_stats['spe']}")
    print(f"🔥 Applied EVs: HP:{pokemon['ev_hp']} ATK:{pokemon['ev_atk']} DEF:{pokemon['ev_def']} SPA:{pokemon['ev_spa']} SPD:{pokemon['ev_spd']} SPE:{pokemon['ev_spe']}")
    
    return pokemon