import re
import itertools


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
        graph.add_edges_from(edges)


def find_package(line):
    return re.search('L.+-', line).group(0)[1:-2]


def find_method(line):
    return re.search('>.+', line).group(0)[1:]


def find_invoke(line):
    return re.search('-\w{5,9}', line).group(0)[1:]
