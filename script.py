import os
from pip._internal.metadata import get_default_environment

import plotly.graph_objects as go
import networkx as nx

def list_dependencies(package_name):
    try:
        # Get the installed package environment
        env = get_default_environment()

        # Find the distribution info for the given package name
        distribution = env.get_distribution(package_name)
        if distribution is None:
            raise ImportError(f"Package '{package_name}' not found.")

        # Access the package's metadata
        metadata = distribution.metadata

        # Get the 'Requires-Dist' field from the metadata
        requires_dist = metadata.get_all('Requires-Dist')
        if requires_dist is None:
            print(f"Package '{package_name}' has no dependencies.")
            return []

        return [k.split(" ")[0] for k in requires_dist]

    except Exception as e:
        print(e)
        return None
import os
from pip._internal.metadata import get_default_environment
import pkg_resources
import os

def get_package_size(package_name):
    try:
        # Get the package distribution
        distribution = pkg_resources.get_distribution(package_name)
        
        # Get the location of the package
        package_location = distribution.location
        if package_location is None:
            raise ImportError(f"Could not determine the location of package '{package_name}'.")

        # Get the package's directory or its egg file
        package_dir = os.path.join(package_location, distribution.project_name)

        if not os.path.exists(package_dir):
            raise ImportError(f"Package directory '{package_dir}' does not exist.")

        # Traverse the package directory and sum up the file sizes
        total_size = 0
        for dirpath, _, filenames in os.walk(package_dir):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)

        return total_size

    except Exception as e:
        print(e)
        return None

def get_installed_packages_with_dependencies():
    env = get_default_environment()
    packages = {}

    for dist in env.iter_installed_distributions():
        package_name = dist.metadata["Name"]
        package_size = get_package_size(package_name)  # Use your size calculation function here
        dependencies = list_dependencies(package_name) or []
        packages[package_name] = {
            'size': package_size,
            'dependencies': dependencies
        }
    
    return packages

def create_dependency_graph(packages):
    # filter no size packages
    packages = {k: v for k, v in packages.items() if v['size'] is not None}

    G = nx.DiGraph()

    for pkg, info in packages.items():
        G.add_node(pkg, size=info['size'])
        for dep in info['dependencies']:
            if dep in packages:
                G.add_edge(pkg, dep)

    return G

def visualize_graph(G):
    pos = nx.spring_layout(G)

    # Extract the package sizes
    sizes = [G.nodes[node]['size'] / 1000 for node in G.nodes]

    edge_x = []
    edge_y = []

    for edge in G.edges:
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines')

    node_x = []
    node_y = []
    for node in G.nodes:
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        marker=dict(
            showscale=True,
            colorscale='YlGnBu',
            size=sizes,
            color=sizes,
            colorbar=dict(
                thickness=15,
                title='Package Size (KB)',
                xanchor='left',
                titleside='right'
            ),
            line_width=2))

    node_text = []
    for node in G.nodes:
        node_text.append(f'{node} ({G.nodes[node]["size"] / (1024 ** 2):.2f} MB)')
    node_trace.text = node_text

    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        title='<br>Package Dependency Graph',
                        titlefont_size=16,
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=0, l=0, r=0, t=40),
                        annotations=[dict(
                            text="Package Dependencies",
                            showarrow=False,
                            xref="paper", yref="paper",
                            x=0.005, y=-0.002 )],
                        xaxis=dict(showgrid=False, zeroline=False),
                        yaxis=dict(showgrid=False, zeroline=False)))

    fig.write_html("dependency_graph.html")

packages = get_installed_packages_with_dependencies()
G = create_dependency_graph(packages)
visualize_graph(G)
