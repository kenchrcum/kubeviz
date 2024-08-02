#!/usr/bin/env python3
import argparse
import subprocess
import os
import tempfile
import pydot  # You can use this library for graph visualization
from kubernetes import client, config


def fetch_daemonsets(namespace):
    config.load_kube_config()  # Load kubeconfig (customize as needed)
    v1 = client.AppsV1Api()
    daemonsets = v1.list_namespaced_daemon_set(namespace=namespace).items
    return daemonsets


def fetch_pods(namespace):
    v1 = client.CoreV1Api()
    pods = v1.list_namespaced_pod(namespace=namespace).items
    return pods


def fetch_deployments(namespace):
    config.load_kube_config()  # Load kubeconfig (customize as needed)
    v1 = client.AppsV1Api()
    deployments = v1.list_namespaced_deployment(namespace=namespace).items
    return deployments


def fetch_statefulsets(namespace):
    v1 = client.AppsV1Api()
    statefulsets = v1.list_namespaced_stateful_set(namespace=namespace).items
    return statefulsets


def fetch_jobs(namespace):
    v1 = client.BatchV1Api()
    jobs = v1.list_namespaced_job(namespace=namespace).items
    return jobs


def fetch_cronjobs(namespace):
    v1 = client.BatchV1Api()
    cronjobs = v1.list_namespaced_cron_job(namespace=namespace).items
    return cronjobs


def create_connections(daemonsets, pods, deployments, statefulsets, jobs, cronjobs):
    connections = {}  # Dictionary to store connections (resource type -> resource name)

    # Example: Connect Deployments to StatefulSets
    for ds in daemonsets:
        for pod in pods:
            # Check if the pod is scheduled by this DaemonSet
            if ds.spec.template.spec.node_selector == pod.spec.node_selector:
                connections.setdefault(ds.metadata.name, []).append(pod.metadata.name)

    for deployment in deployments:
        connections.setdefault('Deployment', []).append(deployment.metadata.name)
    for statefulset in statefulsets:
        connections.setdefault('StatefulSet', []).append(statefulset.metadata.name)

    # Example: Connect Jobs to CronJobs
    for job in jobs:
        connections.setdefault('Job', []).append(job.metadata.name)
    for cronjob in cronjobs:
        connections.setdefault('CronJob', []).append(cronjob.metadata.name)

    # Add other connections as needed

    return connections


def create_joined_graph(connections):
    graph = pydot.Dot(graph_type='digraph')

    # Add nodes for each resource type
    for resource_type, resource_names in connections.items():
        for resource_name in resource_names:
            node = pydot.Node(f"{resource_type}: {resource_name}", shape='box')
            graph.add_node(node)

    # Add edges (connections) between resources
    # Example: Connect Deployment to StatefulSet
    for deployment_name in connections.get('Deployment', []):
        for statefulset_name in connections.get('StatefulSet', []):
            edge = pydot.Edge(f"Deployment: {deployment_name}", f"StatefulSet: {statefulset_name}")
            graph.add_edge(edge)

    # Add other edges as needed

    return graph


def main():
    parser = argparse.ArgumentParser(description='Generate joined Kubernetes architecture diagram')
    parser.add_argument('-n', '--namespace', default='default', help='Kubernetes namespace')
    parser.add_argument('-o', '--outfile', default='k8sviz.png', help='Output filename')
    args = parser.parse_args()

    daemonsets = fetch_daemonsets(args.namespace)
    pods = fetch_pods(args.namespace)
    deployments = fetch_deployments(args.namespace)
    statefulsets = fetch_statefulsets(args.namespace)
    jobs = fetch_jobs(args.namespace)
    cronjobs = fetch_cronjobs(args.namespace)

    connections = create_connections(daemonsets, pods, deployments, statefulsets, jobs, cronjobs)
    joined_graph = create_joined_graph(connections)

    # Save the joined graph (you can customize the filename and format)
    joined_graph.write_png(args.outfile)
    print(f"Joined diagram saved as {args.outfile}")


if __name__ == '__main__':
    main()
