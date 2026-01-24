import functools

from datetime import date as dt
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, jsonify
)


from precon_escalation_league.db import get_db, get_precon_list, get_list_of_commanders, get_list_of_names, post_game, get_precon_autocomplete

bp = Blueprint('submit', __name__)

@bp.before_app_request
def init_autofill():
    get_precon_list()
    get_list_of_names()
    get_list_of_commanders()
    get_precon_autocomplete()

    
    
@bp.route("/decks")
def decks():
    return render_template("precon-league/decks.html")

@bp.route("/")
def frontpage():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Get all games
    cursor.execute("""
        SELECT id, date_played, round
        FROM games
        ORDER BY date_played DESC, round DESC
    """)
    games = cursor.fetchall()

    game_data = []

    for game in games:
        # Get all players for this game with deck & commander names
        cursor.execute("""
            SELECT 
                pl.player_name,
                d.deck_name,
                c.commander_name,
                plc.place,
                plc.turn_order
            FROM places plc
            JOIN players pl ON plc.player_id = pl.id
            JOIN precon_decks d ON plc.deck_used = d.id
            JOIN commanders c ON plc.commander = c.id
            WHERE plc.game_id = %s
            ORDER BY plc.place ASC, plc.turn_order ASC
        """, (game["id"],))

        players = cursor.fetchall()

        game_data.append({
            "id": game["id"],
            "round": game["round"],
            "date": game["date_played"],  # matches schema
            "players": players
        })

    cursor.close()
    return render_template("precon-league/frontpage.html", game_data=game_data)



@bp.route("/submit", methods=["GET", "POST"])
def submit():
    if request.method == "POST":
        try:
            round_num = request.form["round"]
            if not round_num.isdigit() or int(round_num) < 1:
                return jsonify({
                    "ok": False,
                    "error": "Round number is required."
                }), 400
            
            date = request.form["date"]
            if not date:
                return jsonify({
                    "ok": False,
                    "error": "Date is required."
                }), 400
            players = []
            i = 0
            while f"players[{i}][name]" in request.form:
                players.append({
                    "name": request.form[f"players[{i}][name]"],
                    "deck": request.form.get(f"players[{i}][deck]"),
                    "commander": request.form.get(f"players[{i}][commander]"),
                    "place": request.form.get(f"players[{i}][place]"),
                    "turn_order": request.form.get(f"players[{i}][turn_order]"),
                })
                i += 1

            post_game(players, date, round_num)
        except Exception as e:
            return jsonify({
                "ok": False,
                "error": str(e)
            }), 400

    today = dt.today().isoformat()
    return render_template("precon-league/submit.html", today=today, precon_autocomplete=g.precon_autocomplete, commander_list=g.commander_list, name_list=g.name_list)
        