
from flask import Flask, render_template, request, redirect, url_for, flash
import math

app = Flask(__name__)
app.secret_key = "friendmatch-secret-key"

# Sample friendships
SAMPLE = [
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
    ("Zoya", "Yash")
]

# Graph: each user is a node, each friendship is an edge
graph = {}


def add_user(name):
    graph.setdefault(name, set())


def add_friend(a, b):
    add_user(a)
    add_user(b)
    graph[a].add(b)
    graph[b].add(a)


def reset_sample():
    graph.clear()
    for a, b in SAMPLE:
        add_friend(a, b)


def find_name(name):
    for existing in graph:
        if existing.casefold() == name.casefold():
            return existing
    return name


def mutual_friends(a, b):
    return sorted(graph.get(a, set()) & graph.get(b, set()))


def recommend(user, top_n=5):
    """Recommend friends-of-friends ranked by mutual connections."""
    if user not in graph:
        return []

    scores = {}

    for friend in graph[user]:
        for candidate in graph[friend]:
            if candidate != user and candidate not in graph[user]:
                scores[candidate] = scores.get(candidate, 0) + 1

    ranked = sorted(
        scores.items(),
        key=lambda item: (-item[1], item[0].casefold())
    )

    return [
        {
            "name": name,
            "score": score,
            "mutual": mutual_friends(user, name)
        }
        for name, score in ranked[:top_n]
    ]


def graph_data(selected, recommendations):
    names = sorted(graph, key=str.casefold)
    cx, cy = 200, 165
    radius = min(135, 40 + len(names) * 12)
    positions = {}

    for i, name in enumerate(names):
        angle = -math.pi / 2 + 2 * math.pi * i / max(len(names), 1)
        positions[name] = (
            round(cx + radius * 1.2 * math.cos(angle), 2),
            round(cy + radius * math.sin(angle), 2)
        )

    edges = []
    seen = set()

    for person, friends in graph.items():
        for friend in friends:
            key = tuple(sorted((person, friend), key=str.casefold))
            if key not in seen:
                seen.add(key)
                edges.append({
                    "x1": positions[person][0],
                    "y1": positions[person][1],
                    "x2": positions[friend][0],
                    "y2": positions[friend][1]
                })

    rec_names = {r["name"] for r in recommendations}
    nodes = []

    for name in names:
        if name == selected:
            color = "#2f855a"
        elif name in graph.get(selected, set()):
            color = "#2b6cb0"
        elif name in rec_names:
            color = "#c05621"
        else:
            color = "#8a97a6"

        nodes.append({
            "name": name,
            "x": positions[name][0],
            "y": positions[name][1],
            "color": color
        })

    dashed_edges = []
    if selected in positions:
        for name in rec_names:
            if name in positions:
                dashed_edges.append({
                    "x1": positions[selected][0],
                    "y1": positions[selected][1],
                    "x2": positions[name][0],
                    "y2": positions[name][1]
                })

    return edges, dashed_edges, nodes


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        action = request.form.get("action", "")

        if action == "add":
            a = " ".join(request.form.get("person", "").split())
            b = " ".join(request.form.get("friend", "").split())

            if not a or not b:
                flash("Enter both names.", "error")
            elif a.casefold() == b.casefold():
                flash("A person cannot befriend themselves.", "error")
            else:
                a, b = find_name(a), find_name(b)

                if b in graph.get(a, set()):
                    flash("These users are already friends.", "error")
                else:
                    add_friend(a, b)
                    flash(f"Added friendship between {a} and {b}.", "success")
                    return redirect(url_for("index", who=a))

        elif action == "reset":
            reset_sample()
            flash("Sample network restored.", "success")
            return redirect(url_for("index", who="Aarav"))

    names = sorted(graph, key=str.casefold)
    selected = request.args.get("who", "Aarav")

    if selected not in graph and names:
        selected = names[0]

    try:
        top_n = int(request.args.get("top", "5"))
    except ValueError:
        top_n = 5

    if top_n not in (1, 3, 5, 10):
        top_n = 5

    recommendations = recommend(selected, top_n) if selected else []
    edges, dashed_edges, nodes = graph_data(
        selected, recommendations
    ) if names else ([], [], [])

    return render_template(
        "index.html",
        names=names,
        selected=selected,
        top_n=top_n,
        recommendations=recommendations,
        edges=edges,
        dashed_edges=dashed_edges,
        nodes=nodes
    )


reset_sample()

if __name__ == "__main__":
    app.run(debug=True)
