import math

from flask import Flask, render_template_string, request

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Social network graph (adjacency sets, stored in memory)
# ---------------------------------------------------------------------------
graph = {}


def add_user(name):
    graph.setdefault(name, set())


def add_friend(a, b):
    add_user(a)
    add_user(b)
    graph[a].add(b)
    graph[b].add(a)


def mutual_friends(a, b):
    return graph.get(a, set()) & graph.get(b, set())


def recommend(user, top_n=5):
    """Rank friends-of-friends by number of mutual friends."""
    if user not in graph:
        return []

    scores = {}
    for friend in graph[user]:
        for fof in graph[friend]:
            if fof != user and fof not in graph[user]:
                scores[fof] = scores.get(fof, 0) + 1

    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0].lower()))
    return ranked[:top_n]


def build_graph_view(selected, recommended_names):
    """Lay the network out on a circle and return nodes/edges for SVG."""
    names = sorted(graph, key=str.lower)
    cx, cy, radius = 280, 260, 190
    positions = {}
    for i, name in enumerate(names):
        angle = 2 * math.pi * i / max(len(names), 1) - math.pi / 2
        positions[name] = (cx + radius * math.cos(angle), cy + radius * math.sin(angle))

    friends = graph.get(selected, set())
    nodes = []
    for name in names:
        x, y = positions[name]
        if name == selected:
            kind = "me"
        elif name in friends:
            kind = "friend"
        elif name in recommended_names:
            kind = "rec"
        else:
            kind = "other"
        # push the label a bit further out than the dot
        lx = cx + (radius + 28) * (x - cx) / radius
        ly = cy + (radius + 28) * (y - cy) / radius
        nodes.append({"name": name, "x": x, "y": y, "lx": lx, "ly": ly, "kind": kind})

    edges = []
    seen = set()
    for a in graph:
        for b in graph[a]:
            key = tuple(sorted((a, b)))
            if key in seen:
                continue
            seen.add(key)
            hot = selected in key
            edges.append({
                "x1": positions[a][0], "y1": positions[a][1],
                "x2": positions[b][0], "y2": positions[b][1],
                "hot": hot,
            })
    # draw highlighted edges last so they sit on top
    edges.sort(key=lambda e: e["hot"])
    return nodes, edges


# ---------------------------------------------------------------------------
# Sample network
# ---------------------------------------------------------------------------
sample = [
    ("Aarav", "Isha"),
    ("Aarav", "Rohan"),
    ("Aarav", "Neha"),
    ("Isha", "Meera"),
    ("Rohan", "Meera"),
    ("Neha", "Meera"),
    ("Isha", "Kabir"),
    ("Rohan", "Kabir"),
    ("Neha", "Sara"),
    ("Kabir", "Tanvi"),
    ("Sara", "Dev"),
    ("Zoya", "Yash"),
]

for a, b in sample:
    add_friend(a, b)


# ---------------------------------------------------------------------------
# Web page
# ---------------------------------------------------------------------------
HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Friend Recommender</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: Arial, sans-serif;
            background: #f1f5f9;
            margin: 0;
            padding: 25px;
            color: #14202e;
        }
        .container { max-width: 860px; margin: auto; }
        .card {
            background: white;
            padding: 20px;
            margin: 15px 0;
            border-radius: 12px;
            box-shadow: 0 2px 8px #0001;
        }
        h1 { color: #2b6cb0; margin-bottom: 4px; }
        h2 { margin-top: 0; }
        input, select, button {
            padding: 10px;
            margin: 5px 0;
            border: 1px solid #ccc;
            border-radius: 6px;
            font-size: 15px;
        }
        input, select { max-width: 100%; }
        button { background: #2b6cb0; color: white; cursor: pointer; border: none; }
        button:hover { background: #245a94; }
        li { margin: 12px 0; }
        .mutual { color: #64748b; font-size: 14px; }
        .message { font-weight: bold; color: #2b6cb0; }
        .legend span { display: inline-block; margin-right: 14px; font-size: 14px; }
        .dot {
            display: inline-block; width: 11px; height: 11px;
            border-radius: 50%; margin-right: 5px; vertical-align: middle;
        }
        svg { width: 100%; height: auto; display: block; }
        @media (max-width: 600px) {
            body { padding: 12px; }
            .card { padding: 14px; }
        }
    </style>
</head>
<body>
<div class="container">
    <h1>Friend Recommender</h1>
    <p>Discover new friends using mutual connections.</p>

    <div class="card">
        <h2>Find Recommendations</h2>
        <form method="GET">
            <label>Select person:</label><br>
            <select name="user">
                {% for name in names %}
                <option value="{{ name }}" {% if name == selected %}selected{% endif %}>
                    {{ name }}
                </option>
                {% endfor %}
            </select>
            <br>
            <label>Number of recommendations:</label><br>
            <select name="top_n">
                {% for n in [1, 3, 5, 10] %}
                <option value="{{ n }}" {% if n == top_n %}selected{% endif %}>{{ n }}</option>
                {% endfor %}
            </select>
            <br>
            <button type="submit">Recommend Friends</button>
        </form>

        <h3>Recommended Friends</h3>
        {% if recommendations %}
        <ol>
            {% for name, score in recommendations %}
            <li>
                <strong>{{ name }}</strong> &mdash; {{ score }} mutual friend(s)
                <div class="mutual">
                    Mutual friends: {{ mutual(selected, name)|sort|join(', ') }}
                </div>
            </li>
            {% endfor %}
        </ol>
        {% else %}
        <p>No recommendations available.</p>
        {% endif %}
    </div>

    <div class="card">
        <h2>Network Graph</h2>
        <div class="legend">
            <span><i class="dot" style="background:#2b6cb0"></i>Selected</span>
            <span><i class="dot" style="background:#2f9e6b"></i>Friend</span>
            <span><i class="dot" style="background:#e8890c"></i>Recommended</span>
            <span><i class="dot" style="background:#94a3b8"></i>Other</span>
        </div>
        <svg viewBox="0 0 560 520" role="img" aria-label="Friendship network graph">
            {% for e in edges %}
            <line x1="{{ e.x1|round(1) }}" y1="{{ e.y1|round(1) }}"
                  x2="{{ e.x2|round(1) }}" y2="{{ e.y2|round(1) }}"
                  stroke="{{ '#2b6cb0' if e.hot else '#cbd5e1' }}"
                  stroke-width="{{ 2.5 if e.hot else 1.5 }}"/>
            {% endfor %}
            {% for n in nodes %}
            {% set fill = {'me': '#2b6cb0', 'friend': '#2f9e6b', 'rec': '#e8890c', 'other': '#94a3b8'}[n.kind] %}
            <circle cx="{{ n.x|round(1) }}" cy="{{ n.y|round(1) }}"
                    r="{{ 12 if n.kind == 'me' else 9 }}" fill="{{ fill }}"
                    stroke="white" stroke-width="2"/>
            <text x="{{ n.lx|round(1) }}" y="{{ n.ly|round(1) }}"
                  text-anchor="middle" dominant-baseline="middle"
                  font-size="13" fill="#14202e"
                  font-weight="{{ 'bold' if n.kind in ('me', 'rec') else 'normal' }}">{{ n.name }}</text>
            {% endfor %}
        </svg>
    </div>

    <div class="card">
        <h2>Add a Friendship</h2>
        <form method="POST">
            <input name="person" placeholder="Enter person name" required>
            <input name="friend" placeholder="Enter friend name" required>
            <br>
            <button type="submit">Add Friendship</button>
        </form>
        {% if message %}
        <p class="message">{{ message }}</p>
        {% endif %}
    </div>

    <div class="card">
        <h2>Network Members</h2>
        <p>{{ names|join(', ') }}</p>
        <p>Total users: {{ names|length }}</p>
    </div>
</div>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def home():
    message = ""
    selected = request.args.get("user", "Aarav")

    if request.method == "POST":
        a = " ".join(request.form.get("person", "").split())
        b = " ".join(request.form.get("friend", "").split())

        if not a or not b:
            message = "Please enter both names."
        elif a.casefold() == b.casefold():
            message = "A person cannot befriend themselves."
        else:
            # Reuse existing names regardless of letter case
            a = next((n for n in graph if n.casefold() == a.casefold()), a)
            b = next((n for n in graph if n.casefold() == b.casefold()), b)

            if b in graph.get(a, set()):
                message = "These people are already friends."
            else:
                add_friend(a, b)
                message = f"Friendship added: {a} and {b}."
                selected = a  # show the person who was just updated

    names = sorted(graph, key=str.lower)
    if selected not in graph:
        selected = names[0] if names else ""

    try:
        top_n = int(request.args.get("top_n", 5))
    except ValueError:
        top_n = 5
    if top_n not in (1, 3, 5, 10):
        top_n = 5

    recommendations = recommend(selected, top_n)
    nodes, edges = build_graph_view(selected, {n for n, _ in recommendations})

    return render_template_string(
        HTML,
        names=names,
        selected=selected,
        top_n=top_n,
        recommendations=recommendations,
        mutual=mutual_friends,
        message=message,
        nodes=nodes,
        edges=edges,
    )


if __name__ == "__main__":
    app.run(debug=True)
