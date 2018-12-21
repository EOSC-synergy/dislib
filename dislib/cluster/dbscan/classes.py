from collections import defaultdict

import numpy as np
from pycompss.api.task import task


class Region(object):

    def __init__(self, region_id, subset, n_samples, epsilon):
        self.id = region_id
        self.epsilon = epsilon
        self._neighbours = []
        self.subset = subset
        self.n_samples = n_samples
        self.labels = None
        self._neighbour_labels = []
        self._neighbour_ids = []

    def add_neighbour(self, region):
        self._neighbours.append(region)

    def partial_dbscan(self, min_samples, max_samples):
        subsets = [self.subset]
        n_samples = self.n_samples

        # get samples from all neighbouring regions
        for region in self._neighbours:
            subsets.append(region.subset)
            n_samples += region.n_samples

        if n_samples == 0:
            self.labels = np.empty(0)
            return

        # if max_samples is not defined, process all samples in a single task
        if max_samples is None:
            max_samples = n_samples

        # compute the neighbours of each sample using multiple tasks
        neigh_list = []

        for idx in range(0, n_samples, max_samples):
            end_idx = idx + max_samples
            neighs = _compute_neighbours(self.epsilon, idx, end_idx, *subsets)
            neigh_list.append(neighs)

        # compute the label of each sample based on their neighbours
        labels = _compute_labels(min_samples, *neigh_list)
        self.labels = _slice_array(labels, 0, self.n_samples)

        # send labels to each neighbouring region
        start = self.n_samples
        finish = start

        for region in self._neighbours:
            finish += region.n_samples
            neigh_labels = _slice_array(labels, start, finish)
            region.add_labels(neigh_labels, self.id)
            start = finish

    def add_labels(self, labels, region_id):
        self._neighbour_labels.append(labels)
        self._neighbour_ids.append(region_id)

    def get_equivalences(self):
        return _compute_equivalences(self.id, self.labels, self._neighbour_ids,
                                     *self._neighbour_labels)

    def update_labels(self, components):
        self.labels = _update_labels(self.id, self.labels, components)


@task(returns=1)
def _update_labels(region_id, labels, components):
    new_labels = np.full(labels.shape[0], -1, dtype=int)

    for label, component in enumerate(components):
        for key in component:
            if key[:2] == region_id:
                indices = np.argwhere(labels == key[2])
                new_labels[indices] = label

    return new_labels


@task(returns=1)
def _compute_equivalences(region_id, labels, neigh_ids, *labels_list):
    equiv = defaultdict(set)

    for label_idx, label in enumerate(labels):
        if label < 0:
            continue

        key = region_id + (label,)

        if key not in equiv:
            equiv[key] = set()

        for neigh_id, neigh_labels in zip(neigh_ids, labels_list):
            neigh_label = neigh_labels[label_idx]

            if neigh_label >= 0:
                neigh_key = neigh_id + (neigh_label,)
                equiv[key].add(neigh_key)

    return equiv


@task(returns=1)
def _slice_array(arr, start, finish):
    return arr[start:finish]


@task(returns=1)
def _compute_neighbours(epsilon, begin_idx, end_idx, *subsets):
    neighbour_list = []
    samples = _concatenate_subsets(*subsets).samples

    for sample in samples[begin_idx:end_idx]:
        neighbours = np.linalg.norm(samples - sample, axis=1) < epsilon
        neigh_indices = np.where(neighbours)[0]
        neighbour_list.append(neigh_indices)

    return neighbour_list


def _concatenate_subsets(*subsets):
    subset = subsets[0].copy()

    for set in subsets[1:]:
        subset.concatenate(set)

    return subset


@task(returns=1)
def _compute_labels(min_samples, *neighbour_lists):
    final_list = neighbour_lists[0]

    for neighbour_list in neighbour_lists[1:]:
        final_list.extend(neighbour_list)

    clusters = _compute_clusters(final_list, min_samples)
    labels = np.full(len(final_list), -1)

    for cluster_id, sample_indices in enumerate(clusters):
        labels[sample_indices] = cluster_id

    return labels


@task(returns=1)
def _get_neigh_labels(labels, indices):
    return labels[indices[0]:indices[1]]


def _compute_clusters(neigh_list, min_samples):
    visited = []
    clusters = []

    for sample_idx, neighs in enumerate(neigh_list):
        if sample_idx in visited:
            continue

        if neighs.size >= min_samples:
            clusters.append([sample_idx])
            visited.append(sample_idx)
            _visit_neighbours(neigh_list, neighs, visited, clusters,
                              min_samples)

    return clusters


def _visit_neighbours(neigh_list, neighbours, visited, clusters, min_samples):
    to_visit = list(neighbours)

    while len(to_visit) > 0:
        neigh_idx = to_visit.pop()

        if neigh_idx in visited:
            continue

        visited.append(neigh_idx)
        clusters[-1].append(neigh_idx)

        if neigh_list[neigh_idx].size >= min_samples:
            to_visit.extend(neigh_list[neigh_idx])


def _get_connected_components(transitions):
    visited = []
    connected = []
    for node, neighbours in transitions.items():
        if node in visited:
            continue

        connected.append([node])

        _visit_neighbours(transitions, neighbours, visited, connected)
    return connected
