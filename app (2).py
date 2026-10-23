import streamlit as st

st.set_page_config(page_title="Friend Recommender", page_icon="🤝", layout="centered")

# ---------------------------------------------------------------------------
# Social network graph (adjacency sets, kept per browser session)
# ---------------------------------------------------------------------------
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
    ("Zoya", "Yash"),
]


def add_friend(graph, a, b):
    graph.setdefault(a, set()).add(b)
    graph.setdefault(b, set()).add(a)


def mutual_friends(graph, a, b):
    return graph.get(a, set()) & graph.get(b, set())


def recommend(graph, user, top_n=5):
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


def graph_dot(graph, selected, recommended_names):
    """Build a Graphviz DOT string with the selected person highlighted."""
    q = lambda s: '"' + s.replace('"', '\\"') + '"'
    friends = graph.get(selected, set())
    lines = [
        "graph G {",
        '  bgcolor="transparent";',
        '  node [shape=circle, style=filled, fontname="Arial", fontsize=12, fontcolor="white", color="white"];',
        '  edge [color="#94a3b8"];',
    ]
    for name in sorted(graph, key=str.lower):
        if name == selected:
            color = "#2b6cb0"
        elif name in friends:
            color = "#2f9e6b"
        elif name in recommended_names:
            color = "#e8890c"
        else:
            color = "#94a3b8"
        lines.append(f"  {q(name)} [fillcolor=\"{color}\"];")
    seen = set()
    for a in graph:
        for b in graph[a]:
            key = tuple(sorted((a, b)))
            if key in seen:
                continue
            seen.add(key)
            if selected in key:
                lines.append(f'  {q(a)} -- {q(b)} [color="#2b6cb0", penwidth=2.5];')
            else:
                lines.append(f"  {q(a)} -- {q(b)};")
    lines.append("}")
    return "\n".join(lines)


if "graph" not in st.session_state:
    g = {}
    for a, b in SAMPLE:
        add_friend(g, a, b)
    st.session_state.graph = g

graph = st.session_state.graph

# ---------------------------------------------------------------------------
# Sidebar: add a friendship (handled first so the page below is up to date)
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Add a Friendship")
    with st.form("add_friend_form", clear_on_submit=True):
        person = st.text_input("Person name")
        friend = st.text_input("Friend name")
        submitted = st.form_submit_button("Add Friendship")

    if submitted:
        a = " ".join(person.split())
        b = " ".join(friend.split())

        if not a or not b:
            st.warning("Please enter both names.")
        elif a.casefold() == b.casefold():
            st.warning("A person cannot befriend themselves.")
        else:
            # Reuse existing names regardless of letter case
            a = next((n for n in graph if n.casefold() == a.casefold()), a)
            b = next((n for n in graph if n.casefold() == b.casefold()), b)

            if b in graph.get(a, set()):
                st.info("These people are already friends.")
            else:
                add_friend(graph, a, b)
                st.session_state["user"] = a  # show the person just updated
                st.success(f"Friendship added: {a} and {b}.")

names = sorted(graph, key=str.lower)

if st.session_state.get("user") not in graph:
    st.session_state["user"] = "Aarav" if "Aarav" in graph else (names[0] if names else None)

# ---------------------------------------------------------------------------
# Main page
# ---------------------------------------------------------------------------
st.title("🤝 Friend Recommender")
st.write("Discover new friends using mutual connections.")

col1, col2 = st.columns([2, 1])
with col1:
    selected = st.selectbox("Select person", names, key="user")
with col2:
    top_n = st.selectbox("Recommendations", [1, 3, 5, 10], index=2)

recommendations = recommend(graph, selected, top_n)

st.subheader("Recommended Friends")
if recommendations:
    for rank, (name, score) in enumerate(recommendations, start=1):
        mutual = ", ".join(sorted(mutual_friends(graph, selected, name)))
        st.markdown(f"**{rank}. {name}** — {score} mutual friend(s)")
        st.caption(f"Mutual friends: {mutual}")
else:
    st.write("No recommendations available.")

st.subheader("Network Graph")
st.caption("🔵 Selected   🟢 Friend   🟠 Recommended   ⚪ Other")
st.graphviz_chart(graph_dot(graph, selected, {n for n, _ in recommendations}))

st.subheader("Network Members")
st.write(", ".join(names))
st.write(f"Total users: {len(names)}")
st.caption("Friendships are stored in memory for your browser session and reset when the app restarts.")
