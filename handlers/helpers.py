"""
Helper functions for Pokemon battle mechanics.
"""
import random
import asyncio
from handlers.battle_handlers import movetext, status_effects, battle_data, battle_state, room_userids, room


async def hp_bar(current_hp, final_hp):
    """Generate HP bar visualization."""
    if final_hp <= 0:
        return "▓▓▓▓▓▓▓▓▓▓"
    
    percentage = current_hp / final_hp
    filled = int(percentage * 10)
    empty = 10 - filled
    
    bar = "█" * filled + "░" * empty
    return bar


async def accuracy_checker(accuracy, move):
    """Check if a move hits based on accuracy."""
    # Never-miss moves always hit
    if move in ["Swift"]:
        return True
    
    # Generate random number 1-100
    roll = random.randint(1, 100)
    return roll <= accuracy


def interpret_type_effect(multiplier):
    """Interpret type effectiveness multiplier into text."""
    if multiplier == 0:
        return 0, "It doesn't affect the opposing Pokémon!"
    elif multiplier < 1:
        return multiplier, "It's not very effective..."
    elif multiplier > 1:
        return multiplier, "It's super effective!"
    else:
        return multiplier, "Effective"


async def type_modifier(move_type, def_type1, def_type2=None):
    """Calculate type effectiveness multiplier."""
    from battle_handlers import type1_modifier
    
    multiplier = 1.0
    
    # Check against first type
    if move_type in type1_modifier and def_type1 in type1_modifier[move_type]:
        multiplier *= type1_modifier[move_type][def_type1]
    
    # Check against second type if it exists
    if def_type2 and move_type in type1_modifier and def_type2 in type1_modifier[move_type]:
        multiplier *= type1_modifier[move_type][def_type2]
    
    return multiplier


async def damage_calc_fn(level, power, attack, defense, type_mult, move):
    """Calculate damage for a move."""
    if power == 0:
        return 0, False
    
    # Check for critical hit (6.25% chance)
    is_critical = random.randint(1, 16) == 1
    crit_multiplier = 2 if is_critical else 1
    
    # Basic damage formula
    base_damage = ((2 * level / 5 + 2) * power * attack / defense) / 50 + 2
    
    # Apply critical hit
    base_damage *= crit_multiplier
    
    # Apply type effectiveness
    base_damage *= type_mult
    
    # Random variation (85% - 100%)
    random_factor = random.randint(85, 100) / 100
    final_damage = int(base_damage * random_factor)
    
    # Minimum 1 damage if move has power
    if power > 0 and final_damage < 1:
        final_damage = 1
    
    return final_damage, is_critical


async def paralyze_check(move):
    """Check if a paralyze move inflicts paralysis."""
    from battle_handlers import always_paralyze_moves, paralyze_moves30, paralyze_moves10
    
    if move in always_paralyze_moves:
        return True
    elif move in paralyze_moves30:
        return random.randint(1, 100) <= 30
    elif move in paralyze_moves10:
        return random.randint(1, 100) <= 10
    
    return False


async def burn_check(move):
    """Check if a burn move inflicts burn."""
    from battle_handlers import always_burn_moves, burn_moves10
    
    if move in always_burn_moves:
        return True
    elif move in burn_moves10:
        return random.randint(1, 100) <= 10
    
    return False


async def end_of_turn_effects(room_id, p1_id, p2_id, p1_active, p2_active):
    """Apply end-of-turn effects like burn damage."""
    if room_id not in status_effects:
        return False
    
    had_effects = False
    
    # Check P1's burn
    if p1_id in status_effects[room_id]:
        if p1_active in status_effects[room_id][p1_id]["burn"]:
            # Apply burn damage (1/16 of max HP)
            max_hp = battle_data[p1_id]["pokemon"][p1_active]["final_hp"]
            burn_damage = max(1, max_hp // 16)
            old_hp = battle_data[p1_id]["pokemon"][p1_active]["current_hp"]
            new_hp = max(0, old_hp - burn_damage)
            battle_data[p1_id]["pokemon"][p1_active]["current_hp"] = new_hp
            
            burn_text = f"{p1_active.split('_')[0]} is hurt by its burn!"
            movetext[p1_id]["text_sequence"].append(burn_text)
            movetext[p2_id]["text_sequence"].append(f"Opposing {p1_active.split('_')[0]} is hurt by its burn!")
            
            print(f"DEBUG: {p1_active} took {burn_damage} burn damage — HP: {old_hp} → {new_hp}")
            had_effects = True
    
    # Check P2's burn
    if p2_id in status_effects[room_id]:
        if p2_active in status_effects[room_id][p2_id]["burn"]:
            # Apply burn damage (1/16 of max HP)
            max_hp = battle_data[p2_id]["pokemon"][p2_active]["final_hp"]
            burn_damage = max(1, max_hp // 16)
            old_hp = battle_data[p2_id]["pokemon"][p2_active]["current_hp"]
            new_hp = max(0, old_hp - burn_damage)
            battle_data[p2_id]["pokemon"][p2_active]["current_hp"] = new_hp
            
            burn_text = f"{p2_active.split('_')[0]} is hurt by its burn!"
            movetext[p2_id]["text_sequence"].append(burn_text)
            movetext[p1_id]["text_sequence"].append(f"Opposing {p2_active.split('_')[0]} is hurt by its burn!")
            
            print(f"DEBUG: {p2_active} took {burn_damage} burn damage — HP: {old_hp} → {new_hp}")
            had_effects = True
    
    return had_effects


async def search_for_opp_trainer(lobby):
    """Search for opponent in lobby and create room."""
    from battle_handlers import (
        room, room_userids, generate_room_id, 
        battle_state, searchmsg, build_team_buttons
    )
    
    print(f"DEBUG: Searching for opponent in lobby with {len(lobby)} players")
    
    # Wait until we have at least 2 players
    while len(lobby) < 2:
        await asyncio.sleep(1)
    
    # Match first two players
    p1_id = lobby.pop(0)
    p2_id = lobby.pop(0)
    
    print(f"DEBUG: Matched {p1_id} vs {p2_id}")
    
    # Generate room ID
    room_id = await generate_room_id()
    
    # Set up room data
    room[p1_id] = {
        "roomid": room_id,
        "opponent": p2_id,
        "start_msg": searchmsg[p1_id]
    }
    room[p2_id] = {
        "roomid": room_id,
        "opponent": p1_id,
        "start_msg": searchmsg[p2_id]
    }
    
    room_userids[room_id] = {
        "p1": p1_id,
        "p2": p2_id
    }
    
    # Show team selection for both players
    p1_team = battle_state[p1_id]["team"]
    p2_team = battle_state[p2_id]["team"]
    
    mode = battle_state[p1_id]["mode"]
    fmt = battle_state[p1_id]["fmt"]
    
    # Get limit
    if mode == "ranked" and fmt == "singles":
        limit = 3
    elif mode == "ranked" and fmt == "doubles":
        limit = 4
    elif mode == "casual" and fmt == "doubles":
        limit = 6
    elif mode == "casual" and fmt == "singles":
        limit = 6
    else:
        limit = 3
    
    p1_buttons = await build_team_buttons(p1_team, p1_id)
    p2_buttons = await build_team_buttons(p2_team, p2_id)
    
    p1_text = (
        f"╭─「 __**Team Preview (0/{limit} selected)**__ 」\n\n"
        "├「__**Your Team**__」\n\n"
        + "\n".join(f"__**⫸ ⬜ {p.split('_')[0]} ⫷**__" for p in p1_team)
    )
    
    p2_text = (
        f"╭─「 __**Team Preview (0/{limit} selected)**__ 」\n\n"
        "├「__**Your Team**__」\n\n"
        + "\n".join(f"__**⫸ ⬜ {p.split('_')[0]} ⫷**__" for p in p2_team)
    )
    
    await searchmsg[p1_id].edit(p1_text, buttons=p1_buttons)
    await searchmsg[p2_id].edit(p2_text, buttons=p2_buttons)
    
    print(f"DEBUG: Room {room_id} created for {p1_id} vs {p2_id}")

print("Helper functions loaded successfully")
