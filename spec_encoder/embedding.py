from __future__ import print_function

import torch
import torch.nn as nn
from torch.autograd import Variable
from .embedding_waveform import *
from spec_encoder.s2v_lib import S2VLIB, S2VGraph
from common.pytorch_util import weights_init, gnn_spmm, get_torch_version
from common.constants import NUM_GRAMMAR_EDGE_TYPES
import torch.nn.functional as F

class EmbedMeanField(nn.Module):
    def __init__(self, latent_dim, num_node_feats,device, max_lv = 3):
        super(EmbedMeanField, self).__init__()
        self.latent_dim = latent_dim        
        self.num_node_feats = num_node_feats        

        self.max_lv = max_lv
        self.device = device
        self.w_n2l = nn.Linear(num_node_feats, latent_dim)
        # self.mapping = nn.Linear(latent_dim*2, latent_dim)
        self.waveform_encoder = Waveform_encoder(2,512,latent_dim,device)
        self.conv_param_list = []
        self.merge_param_list = []
        for i in range(self.max_lv):
            self.conv_param_list.append(nn.Linear(latent_dim*2, NUM_GRAMMAR_EDGE_TYPES * latent_dim))
            self.merge_param_list.append( nn.Linear(NUM_GRAMMAR_EDGE_TYPES * latent_dim, latent_dim*2) )

        self.conv_param_list = nn.ModuleList(self.conv_param_list)
        self.merge_param_list = nn.ModuleList(self.merge_param_list)

        self.state_gru = nn.GRUCell(latent_dim, latent_dim)

        weights_init(self)

    def forward(self, graph_list, waveform,istraining=True): 
        
        all_embedding, wave_embedding =  self.waveform_embedding(graph_list.pg.node_list, waveform)
        node_feat = S2VLIB.ConcatNodeFeats(graph_list)        
        sp_list = S2VLIB.PrepareMeanField(graph_list)
        node_feat = node_feat.to(self.device)
        sp_list_new = [sp.to(self.device) for sp in sp_list]
        version = get_torch_version()
        if not istraining:
            if version >= 0.4:
                torch.set_grad_enabled(False)
            else:
                node_feat = Variable(node_feat.data, volatile=True).to(self.device)
        
        h = self.mean_field(node_feat, sp_list_new,all_embedding,wave_embedding)

        if not istraining: # recover
            if version >= 0.4:
                torch.set_grad_enabled(True)

        return h

    
    def waveform_embedding(self,node_list,waveform):
        
        wave_embedding = self.waveform_encoder(waveform)
        all_embedding = torch.zeros(len(node_list),wave_embedding[0].size()[1]).to(self.device)
        count = 0
        
        for i in range(len(node_list)):
            if node_list[i].node_type == 'Terminal'and node_list[i].name!='const':
                all_embedding[i] = wave_embedding[count]
                count = count + 1 
        assert count==len(wave_embedding)
        
        return all_embedding,wave_embedding
    
    def mean_field(self, node_feat, sp_list,all_embedding,wave_embedding):
        
        input_node_linear = self.w_n2l(node_feat)
        input_message = input_node_linear + all_embedding
        input_message = torch.cat((input_message, sum(wave_embedding).expand(input_message.size()[0], -1)), dim=1)
        # input_message = self.mapping(input_message)
        input_potential = F.tanh(input_message)

        lv = 0
        cur_message_layer = input_potential
        while lv < self.max_lv:
            conv_feat = self.conv_param_list[lv](cur_message_layer)
            chunks = torch.split(conv_feat, self.latent_dim, dim=1)
            
            msg_list = []
            for i in range(NUM_GRAMMAR_EDGE_TYPES):
                t = gnn_spmm(sp_list[i], chunks[i])
                msg_list.append( t )
            
            msg = F.tanh( torch.cat(msg_list, dim=1) )
            cur_input = self.merge_param_list[lv](msg)# + input_potential

            cur_message_layer = cur_input + cur_message_layer
            # cur_message_layer = self.state_gru(cur_input, cur_message_layer)
            cur_message_layer = F.tanh(cur_message_layer)
            lv += 1

        return cur_message_layer


if __name__ == '__main__':

    table = nn.Embedding(5, 3)
    emb = table(torch.tensor([1, 2, 3]))
    y = emb.new_zeros(1, 3, requires_grad=False)

    print(table(torch.tensor(range(5))))
    print(emb)
    print(y)

