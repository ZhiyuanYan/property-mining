from __future__ import print_function

import os
import sys
import torch
from torch.autograd import Variable
import torch.nn.functional as F
import numpy as np

from common.checker import eval_result
from common.cmd_args import cmd_args
from common.spec_tree import is_tree_complete
from parser_syg.sygus_parser import SyExp
from reward.reward import *
from reward.deduction import *
import math

class RLEnv(object):
    def __init__(self, specsample):
        """

        specsample:
            a SpecSample object containing the SpecTree of the original program

        """
        self.specsample = specsample
        self.pg = specsample.pg
        self.t = 0
        self.generated_tree = SyExp('Start', [])
        self.expand_ls = [self.generated_tree]

    def reset(self):
        self.t = 0
        self.generated_tree = SyExp('Start', [])

    def is_finished(self):
        return len(self.expand_ls) == 0

    def is_finished_generic(self):
        return is_tree_complete(self.specsample.spectree.grammar.nonTerminals, self.generated_tree)

    def get_cfg_mapping(self):
        return self.pg.cfg_mapping

    def get_spec_embedding(self):
        return self.pg.spec_embedding


def rollout(specsample, data_smt ,mem, decoder, rudder, avg_return, device ,num_episode, use_random, eps):

    total_loss = 0.0
    rudder_loss = 0.0
    best_reward = -5.0
    best_tree = None
    acc_reward = 0.0
    tackle_const = False
    # run num_episode times of episode and average out the loss for variance reduction
    for _ in range(num_episode):

        nll_list = []
        value_list = []
        reward_list = []
        const = 0
        previous_reward_same = 0
        env = RLEnv(specsample)
        decoder.reset()
        if cmd_args.use_rudder == 1:
            rudder.reset()

        while not env.is_finished():

            nll, vs , having_const = decoder(env, mem, use_random, False, device , const,  eps=eps)
            # reward = eval_result(env.specsample, env.generated_tree) if env.is_finished() else 0.0
            if having_const== True:
                const = const + 1
            reward,reward_width = reward_cal(data_smt,env.specsample.filename, env.specsample.pg, env.generated_tree,const,previous_reward_same) if env.is_finished() else deduction(env.generated_tree,env.specsample.pg, data_smt.formula_dict[env.specsample.filename.replace('.sl', '')])

                    
            # if(env.generated_tree.to_py()=="x==x"):
            #     print(" ")
            nll_list.append(nll)
            value_list.append(vs)
            if(reward_width!=0):
                reward_list.append(reward_width+reward)
                break
            else:
                if(not env.is_finished()):
                    if(previous_reward_same == reward):
                        reward_list.append(0)
                    else:
                        assert reward<previous_reward_same
                        reward_list.append(reward-previous_reward_same)
                        previous_reward_same = reward
                else:
                    reward_list.append(reward)
            env.t += 1

        true_return = np.sum(reward_list)
        if cmd_args.use_rudder == 1:
            rudder_loss += rudder.get_loss(reward_list)
            reward_list = rudder.integrated_gradient(avg_return, true_return)

        policy_loss, value_loss = actor_critic_loss(nll_list, value_list, reward_list,device)
        total_loss += policy_loss + value_loss

        if true_return > best_reward:
            best_reward = true_return
            best_tree = env.generated_tree
        acc_reward += true_return

    total_loss /= num_episode
    rudder_loss /= num_episode
    acc_reward /= num_episode

    return total_loss, rudder_loss, best_reward, best_tree, acc_reward

def supervised_learning(specsample, mem, decoder, device , label ,eps):
    env = RLEnv(specsample)
    decoder.reset()

    loss = 0
    for step in range(-1, -len(label) - 1, -1):
        nll, vs = decoder(env, mem, False, True, device,label[step],eps=eps)
        loss +=nll
    assert env.is_finished()
    
    return loss


def actor_critic_loss(nll_list, value_list, reward_list,device):
    r = 0.0
    rewards = []
    for t in range(len(reward_list) - 1, -1, -1):
        r = r + reward_list[t]  # accumulated future reward
        rewards.insert(0, r / 10.0)

    policy_loss = 0.0
    targets = []
    for t in range(len(reward_list)):
        adv = rewards[t] - value_list[t].data[0, 0]
        policy_loss += nll_list[t] * adv
        targets.append(Variable(torch.Tensor([[rewards[t]]])).to(device))

    policy_loss /= len(reward_list)

    value_pred = torch.cat(value_list, dim=0)
    targets = torch.cat(targets, dim=0)
    value_loss = F.mse_loss(value_pred, targets)

    return policy_loss, value_loss
