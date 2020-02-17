import re
import itertools
from collections import defaultdict
import os
import lib.create_database as cdb
import pandas as pd
import numpy as np
import networkx as nx


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
            api_call = re.search('L.+', i).group(0)[1:]
            var.append(api_call)


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


def get_A_info(smali_src, number_of_apps):
    apk_api = defaultdict(set)

    # get list of APK names
    names = os.listdir(smali_src)
    names = [file for file in names if (file[0] != '.')]
    names = names[:number_of_apps]
    apis = list()
    for name in names:
        print(name)
        path = os.path.join(smali_src, name)
        # get smali files in each apk
        smalies = cdb.get_smali(path)
        # for all smali files find all api calls
        for s in smalies:
            with open(s) as fh:
                find_api_calls(fh, apis)
    # create relationship dictionary apk: [api1, api2, ... apiN]
    apis = set(apis)
    for api in apis:
        apk_api[name].add(api)
    return apk_api, names, apis


def buildA_matrix(smali_src, number_of_apps, **kwargs):
    print('Build A')
    # get a dictionary of the relationships
    a = get_A_info(smali_src, number_of_apps)
    connection = a[0]
    apks = a[1]
    apis = a[2]

    # map the apks and apis to a unique index
    apk_index = pd.Series(apks)
    api_index = pd.Series(list(apis))

    # construct adjacency matrix
    adjacency = list()
    for i in (apk_index.index):
        name = apk_index.iloc[i]
        adjacency.append([1 if(api_index.iloc[j] in connection[name])
                          else 0 for j in range(len(api_index))])
    return np.matrix(adjacency), api_index, apk_index


def build_B(smali_src, number_of_apps, **kwargs):
    print('Build B')
    smali = cdb.get_smali(smali_src)
    B_graph = nx.Graph()
    same_block = defaultdict(list)
    for f in smali[:number_of_apps * 4000]:
        with open(f) as file:
            blocks = defaultdict(list)
            # build B
            locate_method_blocks(file, blocks)
            for b in blocks:
                key = f + str(b)
                apis = []
                find_api_calls(blocks[b], apis)
                if (len(apis) >= 2):
                    same_block[key] = apis

    create_edges(same_block, B_graph)
    return B_graph


def build_P(smali_src, number_of_apps, **kwargs):
    print('Build P')
    # initalize data
    smali = cdb.get_smali(smali_src)

    P_graph = nx.Graph()
    packageD = defaultdict(list)

    count = 0
    for f in smali[:number_of_apps * 4000]:
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
