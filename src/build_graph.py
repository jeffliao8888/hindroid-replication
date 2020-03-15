import re
import itertools
from collections import defaultdict
import os
import pandas as pd
import numpy as np
import networkx as nx
from glob import glob
import random

import logging
logger = logging.getLogger('debug')
hdlr = logging.FileHandler('/datasets/home/home-01/44/544/zjliao/dsc180a/debug.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.INFO)

DATA_PARAMS = 'config/data-params.json'
TEST_PARAMS = 'config/test-params.json'
CREATE_DATABASE = 'config/create-database.json'
ENV = 'config/env.json'

def get_smali(smali_path):
    '''
    get all filenames in smali_path with .smali
    input: directory
    '''
    return glob('%s/**/*.smali' % smali_path, recursive=True)

def locate_method_blocks(text, blocks):
    '''
    Find code blocks in text and save each line that is in between
    .method & .end method to a dictionary as list of lines
    input: file I/O wrapper
    return : None
    '''
    count = 0
    append = False
    for line in text:
        if('.method' in line):
            append = True
        if('.end method' in line):
            blocks[count].append(line)
            append = False
            count += 1
        if(append):
            blocks[count].append(line)


def find_api_calls(iterable, var):
    '''
    Find api calls in a list of texts and save the api calls into var
    input: iterable (list of texts), var (list to save to)
    '''
    for i in iterable:
        if('invoke-' in i and 'method' not in i):
            try:
                api_call = re.search('L.+', i).group(0)[1:]
                var.append(api_call)
            except:
                pass


def create_edges(dic, graph):
    '''
    Create edges for a graph
    input: relationships in dictionary, graph to add edges to
    '''
    for key in dic:
        edges = [i for i in itertools.combinations(dic[key], 2)]
        # print(edges)
        graph.add_edges_from(edges)


def find_package(line):
    return re.search('L.+-', line).group(0)[1:-2]


def find_method(line):
    return re.search('>.+', line).group(0)[1:]


def find_invoke(line):
    return re.search('-\w{5,9}', line).group(0)[1:]

def create_malware_src(path, mal_source):
    dirs = os.listdir(path)
    mal_source.extend([os.path.join(path, folder) for folder in dirs]) 

def find_malware_src(mal_src):
    # change /correct malware path -> can't find path -> src/***missing_dir_name***/name of app
    mal = os.listdir(mal_src)
    mal = [file for file in mal if (file[0] != '.')]
    mal = [os.path.join(mal_src, name) for name in mal]
    mal_source = list()
    each_mal = list()
    for name in mal:
        create_malware_src(name, mal_source)
    for name in mal_source:
        each_mal.extend([os.path.join(name, malware) for malware in os.listdir(name)])
    random.shuffle(each_mal)
#     print(len(each_mal))
    return each_mal

class malware_detection(object):
    def __init__(self, benign_src, mal_src, num_b, num_m, **kwargs):
        print('get info')
        logger.info('Create malware class')
        self.benign_src = benign_src
        self.mal_src = mal_src
        
        # get list of APK names
        benign = os.listdir(benign_src)
        benign = [file for file in benign if (file[0] != '.')]
        random.shuffle(benign)
        apks = benign[:num_b]       
        logger.info(apks)

        if(num_m > 0):
            print('check malware')
            each_mal = find_malware_src(mal_src)
            each_mal = each_mal[:num_m]
        apks.extend(each_mal)
        self.apks = apks
        logger.info(self.apks)

    def buildA_matrix(self):
        print('Build A')
        logger.info('Build A')
        apk_api = defaultdict(set)
        all_apis = list()
        
        print('extract smali')
        for name in self.apks:
            logger.info(re.search('[\w\d\-\_]+$', name).group(0))
            apis = list()
            try:
                path = os.path.join(self.benign_src, name)
                # get smali files in each apk
                smalies = get_smali(path)
                if(len(smalies) == 0):
                    path = os.path.join(self.mal_src, name)
#                     print(path)
                    smalies = get_smali(path)
            except:
                print('except')
#                 path = os.path.join(self.mal_src, name)
#                 # get smali files in each apk
#                 smalies = get_smali(path)
            # for all smali files find all api calls
            logger.info(path)
            for s in smalies:
                try:
                    with open(s) as fh:
                        find_api_calls(fh, apis)
                except:
                    pass
            all_apis.extend(apis)
            apis = set(apis)
            for api in apis:
                apk_api[name].add(api)
        # get a dictionary of the relationships
#         a = get_A_info(benign_src, mal_src, num_b, num_m)
#         print('got info')

        connection = apk_api
        apis = all_apis
        # map the apks and apis to a unique index
        apk_index = pd.Series(self.apks)
        api_index = pd.Series(pd.Series(list(apis)).unique())
        
        # construct adjacency matrix
        print('build adjacency matrix')
        logger.info('Construct A matrix')
        adjacency = list()
        for i in (apk_index.index):
            name = apk_index.iloc[i]
            adjacency.append([1 if(api_index.iloc[j] in connection[name])
                              else 0 for j in range(len(api_index))])
        return np.matrix(adjacency), api_index, apk_index


    def build_B(self):
        print('Build B')
        logger.info('Build B')
        B_graph = nx.Graph()
        same_block = defaultdict(list)
        for name in self.apks:
#             print(re.search('[\w\d\-\_]+$', name).group(0))
            apis = list()
            try:
                path = os.path.join(self.benign_src, name)
                # get smali files in each apk
                smalies = get_smali(path)
            except:
                path = os.path.join(self.mal_src, name)
                # get smali files in each apk
                smalies = get_smali(path)
                
            # for all smali files find all api calls
            for s in smalies:
                with open(s) as file:
                    blocks = defaultdict(list)
                    # build B
                    locate_method_blocks(file, blocks)
                    for b in blocks:
                        key = s + str(b)
                        apis = []
                        find_api_calls(blocks[b], apis)
                        if (len(apis) >= 2):
                            same_block[key] = apis
        print('create B graph')
        logger.info('Build B Graph')
        create_edges(same_block, B_graph)
        return B_graph


    def build_P(self):
        print('Build P')
        logger.info('Build P')
        P_graph = nx.Graph()
        packageD = defaultdict(list)

        count = 0
        
        for name in self.apks:
#             print(re.search('[\w\d\-\_]+$', name).group(0))
            apis = list()
            try:
                path = os.path.join(self.benign_src, name)
                # get smali files in each apk
                smalies = get_smali(path)
            except:
                path = os.path.join(self.mal_src, name)
                # get smali files in each apk
                smalies = get_smali(path)
        
            for f in smalies:
                with open(f) as file:
                    # build P
                    for line in file:
                        if('invoke-' in line and 'method' not in line):
                            try:
                                if(count < 1000):
                                    api = []
                                    find_api_calls([line], api)
                                    package = find_package(line)
                                    packageD[package].append(api[0])
                                    count += 1
                                else:

                                    create_edges(packageD, P_graph)
                                    packageD = defaultdict(list)
                                    count = 0
                            except:
                                pass
        print('create P graph')
        return P_graph


def buildI(smali_src, number_of_apps, **kwargs):
    print('Build I')
    # initalize data
    smali = cdb.get_smali(smali_src)
    I_graph = nx.Graph()
    invokeD = {'direct': [], 'virtual': [],
               'static': [], 'super': [], 'interface': []}

    for f in smali[:4000]:
        with open(f) as file:
            for line in file:
                if('invoke-' in line and 'method' not in line):
                    api = []
                    find_api_calls([line], api)
                    invoke = find_invoke(line)
                    invokeD[invoke].append(api[0])
    for key in invokeD:
        invokeD[key] = set(invokeD[key])

    create_edges(invokeD, I_graph)
    return I_graph
