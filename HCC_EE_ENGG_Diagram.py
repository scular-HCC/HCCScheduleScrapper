"""
Howard Community College
Engineering (Electrical Engineering Transfer Track)
Prerequisite DAG + Layered Visualization + Semester Plan
"""

import networkx as nx
from graphviz import Digraph
from collections import defaultdict

# ============================================================
# 1. Courses and Categories
# ============================================================

courses = {
    "MATH181": ("MATH 181\nCalculus I", "math"),
    "MATH182": ("MATH 182\nCalculus II", "math"),
    "MATH260": ("MATH 260\nDifferential Equations", "math"),

    "PHYS110": ("PHYS 110/110L\nPhysics I (Calculus)", "physics"),
    "PHYS111": ("PHYS 111/111L\nPhysics II (Calculus)", "physics"),

    "CHEM135": ("CHEM 135/136\nChemistry for Engineers", "chem"),

    "ENES100": ("ENES 100\nIntro to Engineering Design", "engineering"),
    "ENES140": ("ENES 140\nMechanics of Materials", "engineering"),

    "ENEE205": ("ENEE 205\nElectric Circuits", "ee"),
    "ENEE222": ("ENEE 222\nDiscrete Signal Analysis", "ee"),
}

# ============================================================
# 2. Prerequisite Edges
# ============================================================

prereqs = [
    ("MATH181", "MATH182"),
    ("MATH182", "MATH260"),

    ("MATH181", "PHYS110"),
    ("PHYS110", "PHYS111"),
    ("MATH182", "PHYS111"),

    ("CHEM135", "ENES100"),
    ("ENES100", "ENES140"),

    ("PHYS110", "ENEE205"),
    ("PHYS111", "ENEE205"),
    ("MATH182", "ENEE205"),

    ("ENEE205", "ENEE222"),
    ("MATH260", "ENEE222"),
]

# ============================================================
# 3. Build DAG
# ============================================================

G = nx.DiGraph()
G.add_nodes_from(courses)
G.add_edges_from(prereqs)

assert nx.is_directed_acyclic_graph(G)

# ============================================================
# 4. Compute Layers Automatically
# ============================================================

def compute_layers(graph):
    layers = {}
    for node in nx.topological_sort(graph):
        preds = list(graph.predecessors(node))
        layers[node] = 0 if not preds else max(layers[p] for p in preds) + 1
    return layers

layers = compute_layers(G)

# ============================================================
# 5. Color Map
# ============================================================

colors = {
    "math": "#CFE8FF",
    "physics": "#E6D9FF",
    "chem": "#FFF2CC",
    "engineering": "#D9F2D9",
    "ee": "#B6E3A8",
}

# ============================================================
# 6. Graphviz Layered DAG (FIXED)
# ============================================================

dot = Digraph(
    "HCC_EE_Layered_DAG",
    node_attr={"shape": "box", "style": "rounded,filled"}
)
dot.attr(rankdir="LR")

layer_groups = defaultdict(list)
for node, layer in layers.items():
    layer_groups[layer].append(node)

for layer in sorted(layer_groups):
    with dot.subgraph(name=f"cluster_{layer}") as c:
        c.attr(label=f"Layer {layer}")
        for node in layer_groups[layer]:
            label, category = courses[node]
            c.node(node, label=label, fillcolor=colors[category])

for a, b in prereqs:
    dot.edge(a, b)

# Optional render
dot.render("hcc_ee_prereq_dag", format="png", cleanup=True)

print("\nGraphviz DAG object created successfully.")

# ============================================================
# 7. Semester Plan from Layers
# ============================================================

semester_plan = defaultdict(list)
for node, layer in layers.items():
    semester_plan[layer].append(courses[node][0])

print("\n--- Automatically Generated Semester Plan ---")
for semester in sorted(semester_plan):
    print(f"\nSemester {semester + 1}")
    for course in semester_plan[semester]:
        print(f"  - {course}")