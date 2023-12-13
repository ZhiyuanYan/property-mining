from __future__ import print_function

import os
import sys
import numpy as np
import torch
import random
import torch.optim as optim
from itertools import chain
from tqdm import tqdm
# sys.path.append('/data/zhiyuany/property_mining')
from common.cmd_args import cmd_args, tic, toc
from common.checker import eval_result
from common.dataset import Dataset
from common.utils import stat_counter
from generator.rl import RLEnv, rollout, actor_critic_loss,supervised_learning
from spec_encoder.embedding import LSTMEmbed, EmbedMeanField
from rudder.rudder import RewardRedistributionLSTM
import generator.decoder as decoder_rec
import common.constants as constants
from data_from_smt.parser import data_from_smt
from data_from_verilog.parser import data_from_verilog
import time
def main():
    random.seed(cmd_args.seed)
    np.random.seed(cmd_args.seed)
    torch.manual_seed(cmd_args.seed)
    tic()
    device = torch.device("cuda:1" if cmd_args.use_cuda else "cpu")
    os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:1000'    
    # use batchsize=1 for simplicity
    assert cmd_args.rl_batchsize == 1

    # is training meta-learner?
    is_meta_learner = True
    # if cmd_args.single_sample is None:
    #     # assert cmd_args.exit_on_find == 0
    #     assert cmd_args.tune_test == 0
    #     is_meta_learner = True

    #     tqdm.write('learning meta learner')
    # else:
        # if using pre-train for single_sample
    if cmd_args.tune_test == 1:
        assert os.path.isfile(cmd_args.tune_test_encoder)
        assert os.path.isfile(cmd_args.tune_test_decoder)

        tqdm.write('solve single sample with pre-trained model')

    else:
        tqdm.write('solve single sample from scratch')
    if(cmd_args.use_smt_switch):
        data_smt = data_from_smt()
        data_smt.load_smt_switch(cmd_args.data_path)
        template_path = data_smt.dump_to_template(cmd_args.data_path)
        data_smt.S2Vgraph(device)
    else:
        data_smt = data_from_verilog()
        data_smt.load_verilog(cmd_args.data_path)
        template_path = data_smt.dump_to_template(cmd_args.data_path)
        data_smt.S2Vgraph(device)
    
        
    
    dataset = Dataset(template_path)
    numOf_node_type = constants.NUM_OF_TYPE

    # define rudder
    rudder = None
    if cmd_args.use_rudder == 1:
        rudder = RewardRedistributionLSTM(cmd_args.embedding_size)

    # define mem_encoder, decoder and opt
    # mem_encoder = LSTMEmbed(cmd_args.embedding_size, numOf_node_type)


    
    if cmd_args.tune_test == 1:
        checkpoint = torch.load(cmd_args.tune_test_encoder)
        mem_encoder = checkpoint["net"]
        decoder = torch.load(cmd_args.tune_test_decoder)
        mem_encoder = mem_encoder.to(device)
        decoder = decoder.to(device)
        if cmd_args.use_rudder == 1:
            rudder.load_state_dict(torch.load(cmd_args.data_root + '/rudder'))
    else:
        mem_encoder = EmbedMeanField(cmd_args.embedding_size, len(dataset.node_type_dict), device,max_lv=cmd_args.s2v_level)
        mem_encoder = mem_encoder.to(device)
        
        decoder_class = getattr(decoder_rec, cmd_args.decoder_model)
        decoder = decoder_class(cmd_args.embedding_size*2, rudder)
        decoder = decoder.to(device)
    params = [mem_encoder.parameters(), decoder.parameters()]
    if cmd_args.use_rudder == 1:
        params.append(rudder.parameters())
    
    start_epoch = 0
    if cmd_args.tune_test == 1:
        optimizer = checkpoint["optimizer"]
        eps = cmd_args.eps*(cmd_args.eps_decay ** checkpoint["epoch"])
        start_epoch =checkpoint["epoch"]
    else:
        eps = cmd_args.eps
        optimizer = optim.Adam(chain.from_iterable(params), lr=cmd_args.learning_rate)
    for epoch in range(start_epoch, cmd_args.num_epochs):

        epoch_best_reward = -5.0
        epoch_best_root = None
        epoch_acc_reward = 0.0
        epoch_best_loss = 1000
        pbar = tqdm(range(100))
        loss_total = 0
        for k in pbar:

            specsample_ls = dataset.sample_minibatch(cmd_args.rl_batchsize, replacement=True)
            idx = specsample_ls[0].filename.replace(".sl", "")
            
            # start = time.time()    
            mem_batch = mem_encoder(specsample_ls[0],data_smt.formula_dict_tensor[idx])
            # end = time.time() 
            # print(end-start) 
            batch_total_loss = 0.0
            batch_rudder_loss = 0.0
            acc_reward = 0.0
            rudder_loss = 0.0
            best_reward = 0.0
            best_tree = None

            # embedding_offset = 0
            for b in range(cmd_args.rl_batchsize):
                specsample = specsample_ls[b]
                
                # mem = mem_batch[embedding_offset: embedding_offset + specsample.spectree.numOf_nodes, :]
                # embedding_offset += specsample.spectree.numOf_nodes
                if cmd_args.use_supervise == False:
                    # start = time.time()
                    total_loss, rudder_loss, best_reward, best_tree, acc_reward = rollout(specsample, data_smt, mem_batch, decoder,
                                                                                      rudder,
                                                                                      (epoch_acc_reward / (k + 1)),device,
                                                                                      num_episode=cmd_args.num_episode,
                                                                                      use_random=True, eps=eps)
                    # end = time.time()

                    # print(end-start)  
                else:
                    label = data_smt.formula_dict_label[idx]
                    total_loss = supervised_learning(specsample, mem_batch, decoder, device , label ,eps)
                eps *= cmd_args.eps_decay

                epoch_acc_reward += acc_reward / cmd_args.rl_batchsize
                batch_total_loss += total_loss
                batch_rudder_loss += rudder_loss
                if best_reward > epoch_best_reward:
                    epoch_best_reward = best_reward
                    epoch_best_root = best_tree
            # if epoch_best_loss<
            optimizer.zero_grad()
            loss = batch_total_loss / cmd_args.rl_batchsize
            if cmd_args.use_rudder == 1:
                batch_rudder_loss /= cmd_args.rl_batchsize
                loss += batch_rudder_loss
            # start = time.time()
            loss.backward()
            # end = time.time()
            # print(end-start)
            loss_total+=loss
            avg_loss = loss_total/(k+1)
            optimizer.step()
            pbar.set_description('avg reward: %.4f, avg loss: %.4f' % (epoch_acc_reward / (k + 1),avg_loss))


        if is_meta_learner:
            if epoch % 100 == 0:
                state_dict_encoder = {"net": mem_encoder, "optimizer": optimizer, "epoch": epoch}
                torch.save(state_dict_encoder, cmd_args.data_root + '/mem_encoder_' + str(epoch)+'.pth')
                torch.save(decoder, cmd_args.data_root + '/decoder_' + str(epoch)+'.pth')
            state_dict_encoder = {"net": mem_encoder, "optimizer": optimizer, "epoch": epoch}
            torch.save(state_dict_encoder, cmd_args.data_root + '/mem_encoder.pth')
            torch.save(decoder, cmd_args.data_root + '/decoder.pth')
            if cmd_args.use_rudder == 1:
                torch.save(rudder.state_dict(), cmd_args.data_root + '/rudder')

        # tinytest for every 100 epochs
        # specsample_ls = dataset.sample_minibatch(1, replacement=True)
        # idx = specsample_ls[0].filename.replace(".sl", "")
        # mem = mem_encoder(specsample_ls,data_smt.formula_dict_tensor[idx])
        # _, _, _, generated_tree, _ = rollout(specsample_ls[0], data_smt, mem, decoder, rudder,
        #                                   epoch_acc_reward / 100.0, num_episode=1, use_random=True, eps=0.0)

        # print('epoch: %d, average reward: %.4f, Random sample result_r: %.4f' % (
        # epoch, epoch_acc_reward / 100.0, eval_result(specsample_ls[0], generated_tree)))
        print('epoch: %d, average reward: %.4f' % (
        epoch, epoch_acc_reward / 100.0))
        with open(os.path.join(cmd_args.data_root,cmd_args.reward_result_path), 'a+') as f:
            f.write('epoch: %d, average reward: %.4f\n'% (
                epoch, epoch_acc_reward / 100.0))
        path = os.path.join(cmd_args.data_root,"mining_result")
        with open(path, 'a+') as f:
            f.write("Here is the end of the epoches: %d"%(epoch))
        # print('epoch: %d, average reward: %.4f, Random: %s, result_r: %.4f' % (
        # epoch, acc_reward / 100.0, generated_tree, eval_result(specsample_ls[0], generated_tree)))
        # print("best_reward:", best_reward, ", best_root:", best_root)
        # print("best_reward:", best_reward)
        print('specs solved:', len(stat_counter.reported))
    
    
    ###  Here is the test function  ####
        if cmd_args.use_supervise == True:
            specsample_ls = dataset.sample_minibatch(len(dataset.sample_idxes), replacement=False)
            for i in range(len(specsample_ls)):
                specsample = specsample_ls[i]
                idx = specsample_ls[i].filename.replace(".sl", "")
                mem_batch = mem_encoder(specsample,data_smt.formula_dict_tensor[idx])
                total_loss, rudder_loss, best_reward, best_tree, acc_reward = rollout(specsample, data_smt, mem_batch, decoder,
                                                                                            rudder,
                                                                                            (epoch_acc_reward / (k + 1)),device,
                                                                                            num_episode=cmd_args.num_episode,
                                                                                            use_random=True, eps=eps)