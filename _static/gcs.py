"""Source for gcs.png, the Google Cloud Storage service diagram."""

import os

from diagrams import Cluster, Diagram
from diagrams.gcp.compute import KubernetesEngine, Run
from diagrams.gcp.network import CDN, LoadBalancing
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
    "Google Cloud Storage service",
    show=False,
    filename="gcs",
    outformat="png",
    graph_attr=graph_attr,
    node_attr=node_attr,
):
    user = User("End user")
    balancer = LoadBalancing("Google Load Balancer")
    login = Run("Login helper")
    cdn = CDN("Google CDN")
    data = Storage("HiPS data store")

    with Cluster("Kubernetes"):
        ingress = LoadBalancing("NGINX ingress")
        gafaelfawr = KubernetesEngine("Gafaelfawr")

    user >> balancer >> cdn >> data
    user >> balancer >> login >> ingress >> gafaelfawr
    user >> ingress >> gafaelfawr
