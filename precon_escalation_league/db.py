import mysql.connector
from datetime import datetime
import os, zipfile, json
import click
from flask import current_app, g
import json
from tqdm import tqdm
import csv

import requests


def is_commander(row):
    legality_json = row.get("leadershipSkills", "{}")

    try:
        legalities = json.loads(legality_json)
    except json.JSONDecodeError:
        return False

    return legalities.get("commander", False)

def get_db():
    if 'db' not in g:
        g.db = mysql.connector.connect(
            host=current_app.config["MYSQL_HOST"],
            user=current_app.config["MYSQL_USER"],
            password=current_app.config["MYSQL_PASSWORD"],
            database=current_app.config["MYSQL_DATABASE"],
            autocommit=False
        )
    return g.db

def get_precon_list():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        'SELECT deck_name FROM precon_decks ORDER BY deck_name'
    )
    rows = cursor.fetchall()
    cursor.close()

    g.precon_list = [row["deck_name"] for row in rows]

def get_list_of_names():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        'SELECT player_name FROM players ORDER BY player_name'
    )
    rows = cursor.fetchall()
    cursor.close()

    g.name_list = [row["player_name"] for row in rows]

def get_list_of_commanders():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        'SELECT commander_name FROM commanders ORDER BY commander_name'
    )
    rows = cursor.fetchall()
    cursor.close()

    g.commander_list = [row["commander_name"] for row in rows]


    
def init_precon_table():
    db = get_db()
    cursor = db.cursor()
    if os.path.exists('intake/decks'):
        for file in os.listdir('intake/decks'):
            os.remove(os.path.join('intake/decks', file))

    if os.path.exists('intake/AllDeckFiles.zip'):
        with zipfile.ZipFile('intake/AllDeckFiles.zip', 'r') as zip_ref:
            zip_ref.extractall('intake/decks')
    else: 
        raise FileNotFoundError("The file 'intake/AllDeckFiles.zip' was not found.")
    for filename in tqdm(os.listdir('intake/decks'), total=len(os.listdir('intake/decks')), desc="Inserting decks"):
        with open(os.path.join('intake/decks', filename), 'r', encoding='utf-8') as f:
            deck = json.load(f).get("data")
            if deck.get("type") == "Commander Deck":
                cursor.execute(
                    'INSERT IGNORE INTO precon_decks (deck_name) VALUES (%s)',
                    (deck.get("name"),)
                )
    db.commit()
    cursor.close()

def init_legendary_table():
    db = get_db()
    cursor = db.cursor()
    if os.path.exists('intake/AllPrintingsCSVFiles'):
        for file in os.listdir('intake/AllPrintingsCSVFiles'):
            os.remove(os.path.join('intake/AllPrintingsCSVFiles', file))

    if os.path.exists('intake/AllPrintingsCSVFiles.zip'):
        with zipfile.ZipFile('intake/AllPrintingsCSVFiles.zip', 'r') as zip_ref:
            zip_ref.extractall('intake/AllPrintingsCSVFiles')
    else: 
        raise FileNotFoundError("The file 'intake/AllPrintingsCSVFiles.zip' was not found.")

    with open(os.path.join('intake/AllPrintingsCSVFiles', "cards.csv"), 'r', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in tqdm(r, desc="Inserting legendary creatures"):
            if is_commander(row):
                cursor.execute(
                    'INSERT IGNORE INTO commanders (commander_name) VALUES (%s)',
                    (row.get("name"),)
                )

    db.commit()
    cursor.close()
            
            

def link_commanders_to_precons():
    db = get_db()
    cursor = db.cursor()


    commander_map = load_commander_map(db)
    precon_map = load_precon_map(db)

    with open(os.path.join("intake/decks_v2.json"), encoding="utf-8") as f:
        deck_data = json.load(f)

    for deck in tqdm(deck_data, desc="Linking commanders to precons", total=len(deck_data)):
        deck_name = deck["name"]
        precon_id = precon_map.get(deck_name)

        if not precon_id:
            continue  # deck not in DB
        for card in deck["commander"]:
            card_name = card["name"]

            commander_id = commander_map.get(card_name)
            if not commander_id:
                print(f"Commander '{card_name}' not legendary.")
                continue  # not a legendary creature
        

            try:
                cursor.execute(
                    """
                    INSERT INTO precon_commanders (precon_id, commander_id)
                    VALUES (%s, %s)
                    """,
                    (precon_id, commander_id)
                )
            except mysql.connector.errors.IntegrityError:
                pass  # already linked

        for card in deck["cards"]:
            card_name = card["name"]

            commander_id = commander_map.get(card_name)
            if not commander_id:
                continue  # not a legendary creature

            try:
                cursor.execute(
                    """
                    INSERT INTO precon_commanders (precon_id, commander_id)
                    VALUES (%s, %s)
                    """,
                    (precon_id, commander_id)
                )
            except mysql.connector.errors.IntegrityError:
                pass  # already linked

    db.commit()
    cursor.close()



    


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    db = get_db()
    cursor = db.cursor()

    with current_app.open_resource('schema.sql') as f:
        statements = f.read().decode('utf8').split(';')

    for stmt in statements:
        stmt = stmt.strip()
        if stmt:
            cursor.execute(stmt)

    db.commit()
    cursor.close()

@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

@click.command('init-precon-list')
def init_precon_list_command():
    """Initialize the precon list."""
    init_precon_table()
    click.echo('Initialized the precon list.')

@click.command('init-legendary-list')
def init_legendary_list_command():
    """Initialize the legendary  list."""
    init_legendary_table()
    click.echo('Initialized the legendary list.')

@click.command('link-commanders-precons')
def link_commanders_precons_command():
    """Link commanders to precons."""
    link_commanders_to_precons()
    click.echo('Linked commanders to precons.')

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(init_precon_list_command)
    app.cli.add_command(init_legendary_list_command)
    app.cli.add_command(link_commanders_precons_command)

def post_game(data: list, date: datetime, round_num: int):
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        'INSERT INTO games (date_played, round) VALUES (%s, %s)',
        (date, round_num)
    )
    game_id = cursor.lastrowid


    for player in data:
        post_player_in_game(
            cursor,
            game_id,
            player["name"],
            player["commander"],
            player["deck"],
            player["place"],
            player["turn_order"]
        )

    db.commit()
    cursor.close()

def post_player_in_game(cursor, game_id: int, player_name: str, commander_name: str, deck_name: str, place: int, turn_order: int):
    player_id = get_player(player_name)
    commander_id = get_commander(commander_name) if commander_name else None
    deck_id = get_deck(deck_name.split("—")[0].strip()) if deck_name else None

    if commander_id is None and commander_name is not None:
        raise ValueError(f"Commander '{commander_name}' not found in database.")
    if deck_id is None and deck_name is not None:
        raise ValueError(f"Deck '{deck_name}' not found in database.")
    print(turn_order)

    
    if turn_order is not None and turn_order != '':
        print("turn order provided")
        cursor.execute(
            'INSERT INTO places (game_id, player_id, commander, deck_used, place, turn_order) VALUES (%s, %s, %s, %s, %s, %s)',
            (game_id, player_id, commander_id, deck_id, place, turn_order)
        )
    else:
        cursor.execute(
            'INSERT INTO places (game_id, player_id, commander, deck_used, place) VALUES (%s, %s, %s, %s, %s)',
            (game_id, player_id, commander_id, deck_id, place)
        )

def get_player(name: str):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        'SELECT id FROM players WHERE player_name = %s',
        (name,)
    )
    player_id = cursor.fetchone()
    if player_id is None:
        cursor.execute(
            'INSERT INTO players (player_name) VALUES (%s)',
            (name,)
        )
        db.commit()
        player_id = cursor.lastrowid
    else:
        player_id = player_id.get("id")
    cursor.close()
    return player_id

def get_deck(deck_name: str):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        'SELECT id FROM precon_decks WHERE deck_name = %s',
        (deck_name,)
    )
    deck_id = cursor.fetchone().get("id")
    cursor.close()
    return deck_id

def get_commander(commander_name: str):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        'SELECT id FROM commanders WHERE commander_name = %s',
        (commander_name,)
    )
    commander_id = cursor.fetchone().get("id")
    cursor.close()
    return commander_id

def load_commander_map(db):
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id, commander_name FROM commanders")
    commanders = {row["commander_name"]: row["id"] for row in cursor.fetchall()}
    cursor.close()
    return commanders

def load_precon_map(db):
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id, deck_name FROM precon_decks")
    precons = {row["deck_name"]: row["id"] for row in cursor.fetchall()}
    cursor.close()
    return precons

def get_or_create_commander(db, commander_name):
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT id FROM commanders WHERE name = %s",
        (commander_name,)
    )
    row = cursor.fetchone()

    if row:
        commander_id = row["id"]
    else:
        cursor.execute(
            "INSERT INTO commanders (name) VALUES (%s)",
            (commander_name,)
        )
        commander_id = cursor.lastrowid
        db.commit()

    cursor.close()
    return commander_id

def get_precon_autocomplete():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            d.id AS precon_id,
            d.deck_name,
            c.commander_name AS commander_name
        FROM precon_decks d
        LEFT JOIN precon_commanders pc ON pc.precon_id = d.id
        LEFT JOIN commanders c ON c.id = pc.commander_id
        ORDER BY d.deck_name
    """)

    g.precon_autocomplete = cursor.fetchall()
    cursor.close()