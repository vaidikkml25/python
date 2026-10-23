"""
Social Network Friend Recommendation System
Using Graphs and Graph Traversal (BFS)

Users are nodes, friendships are edges.
Recommendations = friends-of-friends ranked by number of mutual connections.
"""

import streamlit as st

st.set_page_config(page_title="Friend Recommendation System", page_icon="🤝", layout="wide")


# ---------------- Core graph logic ----------------
def add_user(graph, name):
    graph.setdefault(name, set())


def add_friend(graph, a, b):
    add_user(graph, a)
    add_user(graph, b)
    graph[a].add(b)
    graph[b].add(a)


def mutual_friends(graph, u1, u2):
    return graph[u1] & graph[u2]


def recommend(graph, user, top_n=5):
    scores = {}
    for friend in graph[user]:
        for fof in graph[friend]:
            if fof != user and fof not in graph[user]:
                scores[fof] = scores.get(fof, 0) + 1
    ranked = sorted(scores.items(), key=lambda x: (-x[1], x[0]))
    return ranked[:top_n]


def demo_graph():
    g = {}
    for a, b in [
        ("Aarav", "Isha"), ("Aarav", "Rohan"), ("Isha", "Meera"), ("Rohan", "Meera"),
        ("Meera", "Kabir"), ("Rohan", "Kabir"), ("Isha", "Sneha"), ("Kabir", "Diya"),
    ]:
        add_friend(g, a, b)
    return g


def to_dot(graph, selected=None, recs=()):
    friends = graph.get(selected, set()) if selected else set()
    lines = ["graph G {", "layout=neato; overlap=false; splines=true;",
             'node [shape=circle, style=filled, fontname="Helvetica", fontsize=11, fillcolor="#E5E7EB", color="#9CA3AF"];',
             'edge [color="#9CA3AF"];']
    for n in graph:
        if n == selected:
            style = 'fillcolor="#6366F1", fontcolor="white", color="#4338CA"'
        elif n in recs:
            style = 'fillcolor="#34D399", color="#059669"'
        elif n in friends:
            style = 'fillcolor="#FDE68A", color="#D97706"'
        else:
            style = ""
        lines.append(f'"{n}" [{style}];')
    seen = set()
    for a in graph:
        for b in graph[a]:
            if (b, a) not in seen:
                seen.add((a, b))
                lines.append(f'"{a}" -- "{b}";')
    lines.append("}")
    return "\n".join(lines)


# ---------------- State ----------------
if "graph" not in st.session_state:
    st.session_state.graph = demo_graph()
graph = st.session_state.graph

# ---------------- Sidebar ----------------
with st.sidebar:
    st.header("⚙️ Build the network")

    new_user = st.text_input("Add a user", placeholder="e.g. Vaidik")
    if st.button("➕ Add user", use_container_width=True):
        name = new_user.strip()
        if name:
            add_user(graph, name)
            st.success(f"Added {name}")
        else:
            st.warning("Enter a name first.")

    st.divider()
    users = sorted(graph)
    if len(users) >= 2:
        a = st.selectbox("User A", users, key="fa")
        b = st.selectbox("User B", users, index=1, key="fb")
        if st.button("🤝 Add friendship", use_container_width=True):
            if a == b:
                st.warning("Pick two different users.")
            elif b in graph[a]:
                st.info("Already friends.")
            else:
                add_friend(graph, a, b)
                st.success(f"{a} ↔ {b}")
    else:
        st.caption("Add at least 2 users to create friendships.")

    st.divider()
    c1, c2 = st.columns(2)
    if c1.button("Load demo", use_container_width=True):
        st.session_state.graph = demo_graph()
        st.rerun()
    if c2.button("Clear all", use_container_width=True):
        st.session_state.graph = {}
        st.rerun()

# ---------------- Main ----------------
st.title("🤝 Social Network Friend Recommendation System")
st.caption("Graphs + BFS (friends-of-friends) ranked by mutual connections")

users = sorted(graph)
edges = sum(len(v) for v in graph.values()) // 2
m1, m2 = st.columns(2)
m1.metric("Users (nodes)", len(users))
m2.metric("Friendships (edges)", edges)

if not users:
    st.info("The network is empty. Add users from the sidebar or click **Load demo**.")
    st.stop()

col_sel, col_n = st.columns([3, 1])
user = col_sel.selectbox("Select a user", users)
top_n = col_n.slider("Top N", 1, 10, 5)

results = recommend(graph, user, top_n)
rec_names = [n for n, _ in results]

tab1, tab2, tab3, tab4 = st.tabs(["🕸️ Network", "✨ Recommendations", "👥 Mutual Friends", "📘 How it works"])

with tab1:
    st.graphviz_chart(to_dot(graph, user, rec_names), use_container_width=True)
    st.markdown("🟣 Selected user &nbsp; 🟡 Current friends &nbsp; 🟢 Recommended &nbsp; ⚪ Others")

with tab2:
    st.subheader(f"Recommended friends for {user}")
    if not results:
        st.info("No recommendations — this user has no friends-of-friends outside their circle yet.")
    for rank, (name, count) in enumerate(results, 1):
        via = ", ".join(sorted(mutual_friends(graph, user, name)))
        with st.container(border=True):
            st.markdown(f"**#{rank} &nbsp; {name}** — {count} mutual friend{'s' if count != 1 else ''}")
            st.caption(f"Via: {via}")

with tab3:
    others = [u for u in users if u != user]
    if others:
        other = st.selectbox("Compare with", others, index=others.index(rec_names[0]) if rec_names else 0)
        common = sorted(mutual_friends(graph, user, other))
        if common:
            st.success(f"Mutual friends of {user} and {other}: {', '.join(common)}")
        else:
            st.info(f"{user} and {other} have no mutual friends.")
    else:
        st.info("Add more users to compare.")

with tab4:
    st.markdown("""
**Idea:** a user's best friend suggestions are people they don't know yet but who are connected to many of their friends.

1. Users are **nodes**, friendships are **undirected edges** (adjacency list using sets).
2. For the chosen user, visit every friend (BFS level 1), then every friend's friends (level 2).
3. Skip the user themself and anyone already a friend.
4. Count how many times each candidate appears — that is the **mutual friend count**.
5. Sort by count (highest first) and return the top N.

**Complexity:** O(Σ deg(friend)) per query, plus O(k log k) to sort k candidates.
""")
    st.code('''def recommend(graph, user, top_n=5):
    scores = {}
    for friend in graph[user]:
        for fof in graph[friend]:
            if fof != user and fof not in graph[user]:
                scores[fof] = scores.get(fof, 0) + 1
    ranked = sorted(scores.items(), key=lambda x: -x[1])
    return ranked[:top_n]''', language="python")
