#!/usr/bin/env python

import sys
import json
import shutil
import networkx as nx


# sys.path.insert(0, 'src')  # add library code to path
from lib.create_database import get_data
import lib.build_graph as bg

DATA_PARAMS = 'config/data-params.json'
TEST_PARAMS = 'config/test-params.json'


def load_params(fp):
    with open(fp) as fh:
        param = json.load(fh)
    return param


def create_graphs(cfg):
    A, apis, apks = bg.buildA_matrix(**cfg)
    B = nx.adjacency_matrix(bg.build_B(**cfg), apis.values)
    P = nx.adjacency_matrix(bg.build_P(**cfg), apis.values)
    I = nx.adjacency_matrix(bg.buildI(**cfg), apis.values)
    return A, B, P, I


def main(targets):
    # make the clean target
    # if 'clean' in targets:
    #     shutil.rmtree('data/temp', ignore_errors=True)
    #     shutil.rmtree('data/out', ignore_errors=True)
    #     shutil.rmtree('data/test', ignore_errors=True)

    # make the data target
    if 'data' in targets:
        cfg = load_params(DATA_PARAMS)
        get_data(**cfg)

    # make the process target
    if 'process' in targets:
        print('Using params')
        cfg = load_params(DATA_PARAMS)
        print('Build graph')
        A, B, P, I = create_graphs(cfg)
        return A, B, P, I

    # make the test-process target
    if 'data-test' in targets:
        print('Using test params')
        cfg = load_params(TEST_PARAMS)
        print('Build graph')
        A, B, P, I = create_graphs(cfg)
        return A, B, P, I


if __name__ == '__main__':
    targets = sys.argv[1:]
    main(targets)
