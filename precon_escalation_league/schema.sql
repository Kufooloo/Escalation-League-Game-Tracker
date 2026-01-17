DROP TABLE IF EXISTS players;
DROP TABLE IF EXISTS games;
DROP TABLE IF EXISTS places;
DROP TABLE IF EXISTS precon_decks;
DROP TABLE IF EXISTS legendary_creatures;


CREATE TABLE legendary_creatures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    commander_name VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name VARCHAR(255) NOT NULL
);

CREATE TABLE games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date_played DATE NOT NULL,
    round INTEGER NOT NULL
);

CREATE TABLE precon_decks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    deck_name VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE places (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    game_id INTEGER NOT NULL,
    place INTEGER NOT NULL,
    turn_order INTEGER,
    deck_used INTEGER NOT NULL,
    commander INTEGER NOT NULL,

    FOREIGN KEY (player_id) REFERENCES players(id),
    FOREIGN KEY (game_id) REFERENCES games(id),
    FOREIGN KEY (deck_used) REFERENCES precon_decks(id),
    FOREIGN KEY (commander) REFERENCES legendary_creatures(id)
);