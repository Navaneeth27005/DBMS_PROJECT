from flask import Flask, render_template, request, g
import sqlite3

app = Flask(__name__)
DATABASE = 'identifier.sqlite'  # Path to your sqlite file


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row  # Makes rows accessible like dicts
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route('/', methods=['GET', 'POST'])
def index():
    stats = None
    db = get_db()

    # Fetch player names and team names separately
    player_names = [row['name'] for row in db.execute('SELECT name FROM Player').fetchall()]
    team_names = [row['team_name'] for row in db.execute('SELECT team_name FROM Team').fetchall()]

    if request.method == 'POST':
        search_type = request.form['search_type']
        name = request.form['name']

        if search_type == 'player':
            stats = db.execute("""
                SELECT 
                    Player.name,
                    Player.age,
                    Player.season_score,
                    COUNT(Played.match_id) AS matches_played
                FROM Player
                LEFT JOIN Played ON Player.player_id = Played.player_id
                WHERE Player.name = ?
                GROUP BY Player.player_id
            """, (name,)).fetchone()

        elif search_type == 'team':
            stats = db.execute("""
                SELECT 
                    Team.team_name,
                    Team.ranking,
                    COUNT(Team_Player.match_id) AS matches_played,
                    SUM(CASE WHEN Team_Player.result = 'Won' THEN 1 ELSE 0 END) AS matches_won
                FROM Team
                LEFT JOIN Team_Player ON Team.team_name = Team_Player.team_name
                WHERE Team.team_name = ?
                GROUP BY Team.team_name
            """, (name,)).fetchone()

    return render_template('index.html',
                           stats=dict(stats) if stats else None,
                           player_names=player_names, team_names=team_names,
                           has_stats=bool(stats))


if __name__ == '__main__':
    app.run(debug=True)
