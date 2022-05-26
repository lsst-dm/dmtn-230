"""Source for web-service.png, the web service architecture diagram."""

import os

from diagrams import Cluster, Diagram, Edge
from diagrams.gcp.compute import KubernetesEngine
from diagrams.gcp.network import LoadBalancing
from diagrams.gcp.storage import Storage
from diagrams.onprem.client import User

os.chdir(os.path.dirname(__file__))

graph_attr = {
    "label": "",
    "nodesep": "0.2",
    "pad": "0.2",
    "ranksep": "0.75",
}

node_attr = {
    "fontsize": "14.0",
}

edge_attr = {
    "fontsize": "10.0",
}

with Diagram(
    "HiPS web service",
    show=False,
    filename="web-service",
    outformat="png",
    graph_attr=graph_attr,
    node_attr=node_attr,
):
    user = User("End user")
    data = Storage("HiPS data store")

    with Cluster("Kubernetes"):
        ingress = LoadBalancing("NGINX ingress")
        gafaelfawr = KubernetesEngine("Gafaelfawr")
        frontend = KubernetesEngine("crawlspace")

    user >> ingress >> frontend >> data
    ingress >> gafaelfawr
