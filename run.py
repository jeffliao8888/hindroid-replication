#!/usr/bin/env python
import sys
import json
import shutil
import networkx as nx
import os, sys, inspect
import numpy as np

from src.create_database import get_data
import src.build_graph as bg

from sklearn.model_selection import train_test_split
from sklearn.svm import SVC

import logging
# command = 'rm ./debug.log'
# os.popen(command)
logger = logging.getLogger('debug')
hdlr = logging.FileHandler('/datasets/home/home-01/44/544/zjliao/dsc180a/debug.log', mode='w')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.INFO)

DATA_PARAMS = 'config/data-params.json'
TEST_PARAMS = 'config/test-params.json'
CREATE_DATABASE = 'config/create-database.json'
ENV = 'config/env.json'

def load_params(fp):
    with open(fp) as fh:
        param = json.load(fh)
    return param

def create_graphs(cfg):
    malware = bg.malware_detection(**cfg)
    A, apis, apks = malware.buildA_matrix()
    B = nx.adjacency_matrix(malware.build_B(), apis)
    P = nx.adjacency_matrix(malware.build_P(), apis)
    
    
#     A, apis, apks = bg.buildA_matrix(**cfg)
#     B = nx.adjacency_matrix(bg.build_B(**cfg), apis.values)
#     P = nx.adjacency_matrix(bg.build_P(**cfg), apis.values)
#     I = nx.adjacency_matrix(bg.buildI(**cfg), apis.values)
    return A, B, P

def AA(a):
    return a * a.T

def ABA(a, b):
    return a * b * a.T

def APA(a, p):
    return a * p * a.T

def APBPA(a, b, p):
    return a * p * b * p.T * a.T

def classification(X_train, y_train, X_test, y_test, B, P):
    clf = SVC(kernel = 'precomputed')
    kernel_train = AA(X_train)
    clf.fit(kernel_train, y_train)
    kernel_test = np.dot(X_test, X_train.T)
    aa = clf.score(kernel_test, y_test)

    clf = SVC(kernel = 'precomputed')
    kernel_train = ABA(X_train, B)
    clf.fit(kernel_train, y_train)
    kernel_test = X_test * B * X_train.T
    aba = clf.score(kernel_test, y_test)

    clf = SVC(kernel = 'precomputed')
    kernel_train = X_train * P * X_train.T
    clf.fit(kernel_train, y_train)
    kernel_test = X_test * P * X_train.T
    apa = clf.score(kernel_test, y_test)

    clf = SVC(kernel = 'precomputed')
    kernel_train = APBPA(X_train, B, P)
    clf.fit(kernel_train, y_train)
    kernel_test = X_test * P * B * P.T * X_train.T
    apbpa = clf.score(kernel_test, y_test)
    return aa, aba, apa, apbpa

def run_project(cfg, outpath):
    print('Build graph')
    logger.info('Build graphs')
    A, B, P = create_graphs(cfg)
    logger.info(A.shape)

    print('Create SVM')
    logger.info('Create SVM')
    x = A
    num_apps = cfg['num_b'] + cfg['num_m']
    y = [1 if(num<num_apps/2) else 0 for num in range(num_apps)]
    X_train, X_test, y_train, y_test = train_test_split(x, y, test_size=0.3)

    print('classification')
    aa, aba, apa, apbpa = classification(X_train, y_train, X_test, y_test, B, P)

    print('making results')
    results = {
        'aa': aa,
        'aba': aba,
        'apa': apa,
        'apbpa': apbpa
    }

    res = json.dumps(results)

    f = open("%s/results.json"%outpath, "w")
    f.write(res)
    f.close()
    print('results saved')
    logger.info('results saved')

def main(targets):
    # make the clean target
    if 'clean' in targets:
#         shutil.rmtree('data/', ignore_errors=True)
#         shutil.rmtree('data/smali', ignore_errors=True)
#         shutil.rmtree('data/xml', ignore_errors=True)
        command = 'rm -r ./data'
        os.popen(command)
        
    # make the data target
    if 'data' in targets:
        cfg = load_params(CREATE_DATABASE)
        print('get %d apps'%(cfg['num_b'] + cfg['num_m']))
        get_data(**cfg)

    # make the process target
    if 'process' in targets:
        print('Loading params')
        logger.info('Load params')
        cfg = load_params(DATA_PARAMS)
        env = load_params(ENV)
        outpath = env["output-paths"]
        
        run_project(cfg, outpath)
        return 


    # make the test-process target
    if 'data-test' in targets:
        print('Loading params')
        logger.info('Load params')
        cfg = load_params(TEST_PARAMS)
        env = load_params(ENV)
        outpath = env["output-paths"]
        
        run_project(cfg, outpath)
        return 


if __name__ == '__main__':
    targets = sys.argv[1:]
    main(targets)
