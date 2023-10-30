from __future__ import print_function

import json
import sys
import os
from os.path import join as joinpath
import random
import numpy as np

from common.cmd_args import cmd_args
from common.spec_tree import SygusInstance, SpecTree
from common.grammar_graph_builder import GrammarGraph

from spec_encoder.s2v_lib import S2VLIB, S2VGraph


class SpecGrammarSample(S2VGraph):
    def __init__(self, sample_index, db, pg, filename,node_type_dict):
        super(SpecGrammarSample, self).__init__(pg, node_type_dict)
        self.sample_index = sample_index
        self.db = db    
        self.filename = filename    


class Dataset(object):
    def __init__(self,path):
        self.spec_list = []
        self.grammar_list = []
        self.sample_specs = []
        self.file_names = []
        self.path = path
        self.setup_waveform(SpecGrammarSample)

    def load_spec_list(self, fname):
        with open(fname) as f:
            lines = f.read().splitlines()
            res = []
            for l in lines:
                res.append(l)
            content = "\n".join(res)
            sygus_instance = SygusInstance(content)
            # self.spec_list.append(SpecTree(sygus_instance))
            self.grammar_list.append( GrammarGraph(sygus_instance) )

    
    def setup_waveform(self, classname):
        filename = os.path.basename(cmd_args.data_path)
        file_without_extension = os.path.splitext(filename)[0]
        path_for_fname = os.path.join(self.path)
        if cmd_args.single_sample is None:
            for root, dirs, files in os.walk(path_for_fname):
                for file in files:
                    file_path = os.path.join(root, file)
                    self.file_names.append(file)
                    self.load_spec_list(file_path)
        else:
            for root, dirs, files in os.walk(path_for_fname):
                for file in files:
                    if(file==cmd_args.single_sample):
                        file_path = os.path.join(root, file)
                        self.file_names.append(file)
                        self.load_spec_list(file_path)
                    

        self.build_node_type_dict()

        for i in range(len(self.grammar_list)):
            pg = self.grammar_list[i]
            filename = self.file_names[i]
            self.sample_specs.append( classname(i, self, pg, filename ,self.node_type_dict) )
 
        self.sample_idxes = list(range(len(self.sample_specs)))
        random.shuffle(self.sample_idxes)
        self.sample_pos = 0

    def build_node_type_dict(self):
        self.node_type_dict = {}
        
        for g in self.grammar_list:
            for node in g.node_list:
                if not node.node_type in self.node_type_dict:
                    v = len(self.node_type_dict)
                    self.node_type_dict[node.node_type] = v        

    def sample_minibatch(self, num_samples, replacement=False):        
        # if cmd_args.single_sample is not None:
            # return [self.sample_specs[cmd_args.single_sample]]

        s_list = []
        if replacement:
            for i in range(num_samples):
                idx = np.random.randint(len(self.grammar_list))
                s_list.append(self.sample_specs[idx])
        else:
            assert num_samples <= len(self.sample_idxes)
            if num_samples == len(self.sample_idxes):
                return self.sample_specs

            if self.sample_pos + num_samples > len(self.sample_idxes):
                random.shuffle(self.sample_idxes)
                self.sample_pos = 0

            for i in range(self.sample_pos, self.sample_pos + num_samples):
                s_list.append(self.sample_specs[ self.sample_idxes[i]])
            self.sample_pos == num_samples

        return s_list


if __name__ == '__main__':
    dataset = Dataset()
