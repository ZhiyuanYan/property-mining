import tqdm
import sys
from common.cmd_args import cmd_args
from reward.deduction import *
import os
import random 
import itertools
from reward.third_party import run_pono, check_boolector
from parser_syg.sygus_parser import *
from sklearn.cluster import KMeans
import numpy as np
import warnings
from sklearn.exceptions import ConvergenceWarning
import shutil
mining_collection = {}


class BreakAllLoops(Exception):
    pass

def bitwise_subtraction(a, b, bit_width=None):
     # tranfer string to int 
     int_a = int(a, 2)
     int_b = int(b, 2)
     if bit_width is None:
          bit_width = max(len(a), len(b))
     
     assert len(a)== len(b)
     # calculate the substraction
     borrow = 0
     result = 0
     for i in range(bit_width):
          bit_a = (int_a >> i) & 1
          bit_b = (int_b >> i) & 1

          # tackle the borrow
          if bit_a < bit_b + borrow:
               bit_result = 2 + bit_a - bit_b - borrow
               borrow = 1
          else:
               bit_result = bit_a - bit_b - borrow
               borrow = 0

          # calculate the result
          result |= bit_result << i

     # to string
     result_string = "{:0{}b}".format(result, bit_width) if bit_width is not None else bin(result)[2:]

     return result_string

def bitwise_addition(a, b, bit_width=None):
     assert len(a) == len(b), "Input strings must have the same length"
     int_a = int(a, 2)
     int_b = int(b, 2)
     if bit_width is None:
          bit_width = max(len(a), len(b))
     assert len(a)== len(b)
     # Calculate bitwise addition
     carry = int_a & int_b
     result = int_a ^ int_b
     while carry != 0:
          carry_shifted = carry << 1
          carry = result & carry_shifted
          result ^= carry_shifted

     # Limit the bit width of the result
     mask = (1 << bit_width) -1
     result &= mask
     
     result_string = "{:0{}b}".format(result, bit_width)
     return result_string

def bitwise_or(a, b, bit_width=None):
     assert len(a) == len(b), "Input strings must have the same length"
     int_a = int(a, 2)
     int_b = int(b, 2)

     bit_width = max(len(a), len(b))
     assert len(a)== len(b)
     # Calculate bitwise addition

     result = int_a | int_b

     # Limit the bit width of the result
     mask = (1 << bit_width) -1
     result &= mask
     
     result_string = "{:0{}b}".format(result, bit_width)
     return result_string

def bitwise_and(a, b, bit_width=None):
     assert len(a) == len(b), "Input strings must have the same length"
     int_a = int(a, 2)
     int_b = int(b, 2)

     bit_width = max(len(a), len(b))
     assert len(a)== len(b)
     # Calculate bitwise addition

     result = int_a & int_b

     # Limit the bit width of the result
     mask = (1 << bit_width) -1
     result &= mask
     
     result_string = "{:0{}b}".format(result, bit_width)
     return result_string


def bitwise_xor(a, b, bit_width=None):
    assert len(a) == len(b), "Input strings must have the same length"

#     if bit_width is None:
    bit_width = len(a)
#     else:
#         bit_width = max(bit_width, len(a))

    # Convert binary strings to integers
    int_a = int(a, 2)
    int_b = int(b, 2)

    # Calculate bitwise XOR
    result = int_a ^ int_b

    # Limit the bit width of the result
    mask = (1 << bit_width) -1
    result &= mask

    # Convert the result back to a binary string with the specified width
    result_string = format(result, f"0{bit_width}b")

    return result_string

def static_analysis_eq(result):
     count_dict = {}
     if isinstance(result, dict):
          count = 0
          max = ''
          min = ''
          for binary_string in result.values():
               if count == 0:
                    max = binary_string
                    min = binary_string
                    count += 1 
               else:
                    if (int(max,2) < int(binary_string,2)):
                         max = binary_string
                    elif(int(min,2) > int(binary_string,2)):
                         min = binary_string
               if binary_string in count_dict:
                    count_dict[binary_string] += 1
               else:
                    count_dict[binary_string] = 1
     else:
          assert isinstance(result, list)
          count = 0
          max = ''
          min = ''
          for binary_string in result:
               if count == 0:
                    max = binary_string
                    min = binary_string
                    count += 1 
               else:
                    if (int(max,2) < int(binary_string,2)):
                         max = binary_string
                    elif(int(min,2) > int(binary_string,2)):
                         min = binary_string
               if binary_string in count_dict:
                    count_dict[binary_string] += 1
               else:
                    count_dict[binary_string] = 1          
     
     num_to_keep = int(cmd_args.const_threshold * len(count_dict))
     if num_to_keep == 0:
          num_to_keep = 1
     sorted_count_dict = dict(sorted(count_dict.items(), key=lambda item: item[1], reverse=True)[:num_to_keep])
     sort_list = list(sorted_count_dict.keys()) 
     if(max not in sort_list):
          sort_list.append(max)
     if(min not in sort_list):
          sort_list.append(min)     
     return sort_list

def static_analysis_lt(result):
     
     features = [int(binary_string, 2) for binary_string in result.values()]
     std_collect = []
     cand_dict = {}
     warnings.filterwarnings("error", category=ConvergenceWarning)
     for k in range(1,3):
          # 创建K-means模型
          
          try:
               kmeans = KMeans(n_clusters=k)

               # 进行聚类
               kmeans.fit(np.array(features).reshape(-1, 1))  # 需要将特征转换为二维数组
          except ConvergenceWarning:
               raise ValueError("ConvergenceWarning: Number of distinct clusters is smaller than n_clusters")
          # 获取每个二进制字符串所属的簇
          cluster_labels = kmeans.labels_

          # 创建一个字典，将每个二进制字符串分配到对应的簇
          cluster_dict = {}
          for i, (key, binary_string) in enumerate(result.items()):
               cluster_label = cluster_labels[i]
               if cluster_label not in cluster_dict:
                    cluster_dict[cluster_label] = []
               cluster_dict[cluster_label].append((key, binary_string))

          # 计算每个簇的标准差
          cluster_std = 0.0
          for cluster_label, cluster_data in cluster_dict.items():
               cluster_features = [int(binary_string, 2) for _, binary_string in cluster_data]
               cluster_std_single = np.std(cluster_features)
               cluster_std += cluster_std_single
          cluster_std_avg = cluster_std / k
          std_collect.append(cluster_std_avg)
          deviation = 1
          if(k>1):
               deviation = (std_collect[-2] - std_collect[-1]) / (std_collect[-2])
          if((deviation<0.1) or (cluster_std_avg==0)):
               for cluster_label, cluster_data in cluster_dict.items():
                    cluster_features = [int(binary_string, 2) for _, binary_string in cluster_data]
                    width = len(cluster_data[0][1])
                    if cluster_features:
                         max_value = max(cluster_features)
                         min_value = min(cluster_features)
                         binary_max = format(max_value, '0' + str(width) + 'b')
                         binary_min = format(min_value, '0' + str(width) + 'b')
                         cand_dict[binary_max] = cluster_label
                         cand_dict[binary_min] = cluster_label
                    else:
                         # 如果簇为空，设置最大值和最小值为 None 或其他合适的值
                         max_value = None
                         min_value = None       
               return list(cand_dict.keys())
     
     
     for cluster_label, cluster_data in cluster_dict.items():
          cluster_features = [int(binary_string, 2) for _, binary_string in cluster_data]
          width = len(cluster_data[0][1])
          if cluster_features:
               max_value = max(cluster_features)
               min_value = min(cluster_features)
               binary_max = format(max_value, '0' + str(width) + 'b')
               binary_min = format(min_value, '0' + str(width) + 'b')
               cand_dict[binary_max] = cluster_label
               cand_dict[binary_min] = cluster_label
          else:
               # 如果簇为空，设置最大值和最小值为 None 或其他合适的值
               max_value = None
               min_value = None       
     return list(cand_dict.keys())



def recursive_calculation(dic_value, pg, generate_tree, cand_const_add, cand_const_sub,cand_masking):

     symbol = generate_tree.app
     result = []
     result_expand = []
     # extract_flag = False
     if(is_terminal(pg,symbol)):
          result_dict = {}
          result_temp = {}
          if('const' in symbol):
               random_key = random.choice(list(dic_value.keys()))
               for i in range(len(dic_value[random_key])):
                    result_temp[i] = symbol
          else:
               for i in range(len(dic_value[symbol])):
                    result_temp[i] = dic_value[symbol][i]
          result_dict["result"] = result_temp
          return [result_dict]

     if(len(generate_tree.args)==2):
          result_arg_1 = recursive_calculation( dic_value, pg, generate_tree.args[0], cand_const_add, cand_const_sub,cand_masking)
          result_arg_2 = recursive_calculation( dic_value, pg, generate_tree.args[1], cand_const_add, cand_const_sub,cand_masking)
          # assert len(result_arg_1) == len(result_arg_2) 
     
     if(symbol == 'eq'):
          random_key_1 = random.choice(list(result_arg_1[0]["result"].keys()))
          random_key_2 = random.choice(list(result_arg_2[0]["result"].keys()))
          ## Having const
          # const_candidate = []
          if('const' in result_arg_1[0]["result"][random_key_1]):
               assert len(result_arg_1[0]) == 1
               for j in range(len(result_arg_2)):
                    candidate = static_analysis_eq(result_arg_2[j]["result"])
                    result_expand = []
                    for cand in candidate:
                         new_result_temp = {}
                         for i in range(len(result_arg_1[0]["result"])):
                              new_result_temp[i] = cand
                         result_expand.append(new_result_temp)
                    
                    for i in range(len(result_expand)):
                         # for j in range(len(result_arg_2)):
                              assert len(result_expand[i]) == len(result_arg_2[j]["result"])
                              temp_dict = {}
                              result_temp = {}
                              for k in range(len(result_expand[i])):
                                   if(result_expand[i][k]==result_arg_2[j]["result"][k]):
                                        temp_dict[k] = '1' 
                                   else:
                                        temp_dict[k] = '0'
                              result_temp["result"] = temp_dict
                              result_temp[result_arg_1[0]["result"][random_key_1]] = result_expand[i]
                         
                              for previous_const, value in result_arg_2[j].items():
                                   if previous_const == "result":
                                        continue
                                   result_temp[previous_const] = value
                              result.append(result_temp) 
          
          elif('const' in result_arg_2[0]["result"][random_key_2]):
               assert len(result_arg_2) == 1
               for j in range(len(result_arg_1)):
                    candidate = static_analysis_eq(result_arg_1[j]["result"])
                    # const_candidate = list(set(candidate + const_candidate))
                    result_expand = []
                    for cand in candidate:
                         new_result_temp = {}
                         for i in range(len(result_arg_2[0]["result"])):
                              new_result_temp[i] = cand
                         result_expand.append(new_result_temp)
                    
                    for i in range(len(result_expand)):
                         # for j in range(len(result_arg_1)):
                              assert len(result_expand[i]) == len(result_arg_1[j]["result"])
                              temp_dict = {}
                              result_temp = {}
                              for k in range(len(result_expand[i])):
                                   if(result_expand[i][k]==result_arg_1[j]["result"][k]):
                                        temp_dict[k] = '1' 
                                   else:
                                        temp_dict[k] = '0'
                              result_temp["result"] = temp_dict
                              result_temp[result_arg_2[0]["result"][random_key_1]] = result_expand[i]
                         
                              for previous_const, value in result_arg_1[j].items():
                                   if previous_const == "result":
                                        continue
                                   result_temp[previous_const] = value
                              result.append(result_temp)        
          else:
               for i in range(len(result_arg_2)):
                    for j in range(len(result_arg_1)):
                         assert len(result_arg_2[i]["result"]) == len(result_arg_1[j]["result"])
                         temp_dict = {}
                         result_temp = {}
                         for k in range(len(result_arg_2[i]["result"])):
                              if(result_arg_2[i]["result"][k]==result_arg_1[j]["result"][k]):
                                   temp_dict[k] = '1' 
                              else:
                                   temp_dict[k] = '0'
                         result_temp["result"] = temp_dict
                    
                         for previous_const, value in result_arg_2[i].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         for previous_const, value in result_arg_1[j].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         result.append(result_temp) 

     elif(symbol == 'bvule'):
          random_key_1 = random.choice(list(result_arg_1[0]["result"].keys()))
          random_key_2 = random.choice(list(result_arg_2[0]["result"].keys()))
          # const_candidate = []
          ## Having const
          if('const' in result_arg_1[0]["result"][random_key_1]):
               assert len(result_arg_1) == 1
               for j in range(len(result_arg_2)):
                    candidate = static_analysis_lt(result_arg_2[j]["result"])
                    # const_candidate[i] = list(set(candidate + const_candidate))
                    result_expand = []
                    for cand in candidate:
                         new_result_temp = {}
                         for i in range(len(result_arg_1[0]["result"])):
                              new_result_temp[i] = cand
                         result_expand.append(new_result_temp)
               
                    for i in range(len(result_expand)):
                         # for j in range(len(result_arg_2)):
                              assert len(result_expand[i]) == len(result_arg_2[j]["result"])
                              temp_dict = {}
                              result_temp = {}
                              for k in range(len(result_expand[i])):
                                   if(int(result_expand[i][k],2)<=int(result_arg_2[j]["result"][k],2)):
                                        temp_dict[k] = '1' 
                                   else:
                                        temp_dict[k] = '0'
                              result_temp["result"] = temp_dict
                              result_temp[result_arg_1[0]["result"][random_key_1]] = result_expand[i]
                         
                              for previous_const, value in result_arg_2[j].items():
                                   if previous_const == "result":
                                        continue
                                   result_temp[previous_const] = value
                              result.append(result_temp) 
          
          elif('const' in result_arg_2[0]["result"][random_key_2]):
               assert len(result_arg_2) == 1
               for j in range(len(result_arg_1)):
                    candidate = static_analysis_lt(result_arg_1[j]["result"])
                    # const_candidate = list(set(candidate + const_candidate))
                    result_expand = []
                    for cand in candidate:
                         new_result_temp = {}
                         for i in range(len(result_arg_2[0]["result"])):
                              new_result_temp[i] = cand
                         result_expand.append(new_result_temp)
                    
                    for i in range(len(result_expand)):
                         # for j in range(len(result_arg_1)):
                              assert len(result_expand[i]) == len(result_arg_1[j]["result"])
                              temp_dict = {}
                              result_temp = {}
                              for k in range(len(result_expand[i])):
                                   if(int(result_expand[i][k],2)>=int(result_arg_1[j]["result"][k],2)):
                                        temp_dict[k] = '1' 
                                   else:
                                        temp_dict[k] = '0'
                              result_temp["result"] = temp_dict
                              result_temp[result_arg_2[0]["result"][random_key_1]] = result_expand[i]
                         
                              for previous_const, value in result_arg_1[j].items():
                                   if previous_const == "result":
                                        continue
                                   result_temp[previous_const] = value
                              result.append(result_temp)          
          else:
               for i in range(len(result_arg_2)):
                    for j in range(len(result_arg_1)):
                         assert len(result_arg_2[i]["result"]) == len(result_arg_1[j]["result"])
                         temp_dict = {}
                         result_temp = {}
                         for k in range(len(result_arg_2[i]["result"])):
                              if(int(result_arg_2[i]["result"][k],2)>=int(result_arg_1[j]["result"][k],2)):
                                   temp_dict[k] = '1' 
                              else:
                                   temp_dict[k] = '0'
                         result_temp["result"] = temp_dict
                         for previous_const, value in result_arg_2[i].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         for previous_const, value in result_arg_1[j].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         result.append(result_temp) 


     elif(symbol == 'bvuge'):
          random_key_1 = random.choice(list(result_arg_1[0]["result"].keys()))
          random_key_2 = random.choice(list(result_arg_2[0]["result"].keys()))
          # const_candidate = []
          ## Having const
          if('const' in result_arg_1[0]["result"][random_key_1]):
               assert len(result_arg_1) == 1
               for j in range(len(result_arg_2)):
                    candidate = static_analysis_lt(result_arg_2[j]["result"])
                    # const_candidate[i] = list(set(candidate + const_candidate))
                    result_expand = []
                    for cand in candidate:
                         new_result_temp = {}
                         for i in range(len(result_arg_1[0]["result"])):
                              new_result_temp[i] = cand
                         result_expand.append(new_result_temp)
               
                    for i in range(len(result_expand)):
                         # for j in range(len(result_arg_2)):
                              assert len(result_expand[i]) == len(result_arg_2[j]["result"])
                              temp_dict = {}
                              result_temp = {}
                              for k in range(len(result_expand[i])):
                                   if(int(result_expand[i][k],2)>=int(result_arg_2[j]["result"][k],2)):
                                        temp_dict[k] = '1' 
                                   else:
                                        temp_dict[k] = '0'
                              result_temp["result"] = temp_dict
                              result_temp[result_arg_1[0]["result"][random_key_1]] = result_expand[i]
                         
                              for previous_const, value in result_arg_2[j].items():
                                   if previous_const == "result":
                                        continue
                                   result_temp[previous_const] = value
                              result.append(result_temp) 
          
          elif('const' in result_arg_2[0]["result"][random_key_2]):
               assert len(result_arg_2) == 1
               for j in range(len(result_arg_1)):
                    candidate = static_analysis_lt(result_arg_1[j]["result"])
                    # const_candidate = list(set(candidate + const_candidate))
                    result_expand = []
                    for cand in candidate:
                         new_result_temp = {}
                         for i in range(len(result_arg_2[0]["result"])):
                              new_result_temp[i] = cand
                         result_expand.append(new_result_temp)
                    
                    for i in range(len(result_expand)):
                         # for j in range(len(result_arg_1)):
                              assert len(result_expand[i]) == len(result_arg_1[j]["result"])
                              temp_dict = {}
                              result_temp = {}
                              for k in range(len(result_expand[i])):
                                   if(int(result_expand[i][k],2)<=int(result_arg_1[j]["result"][k],2)):
                                        temp_dict[k] = '1' 
                                   else:
                                        temp_dict[k] = '0'
                              result_temp["result"] = temp_dict
                              result_temp[result_arg_2[0]["result"][random_key_1]] = result_expand[i]
                         
                              for previous_const, value in result_arg_1[j].items():
                                   if previous_const == "result":
                                        continue
                                   result_temp[previous_const] = value
                              result.append(result_temp)          
          else:
               for i in range(len(result_arg_2)):
                    for j in range(len(result_arg_1)):
                         assert len(result_arg_2[i]["result"]) == len(result_arg_1[j]["result"])
                         temp_dict = {}
                         result_temp = {}
                         for k in range(len(result_arg_2[i]["result"])):
                              if(int(result_arg_2[i]["result"][k],2)<=int(result_arg_1[j]["result"][k],2)):
                                   temp_dict[k] = '1' 
                              else:
                                   temp_dict[k] = '0'
                         result_temp["result"] = temp_dict
                         for previous_const, value in result_arg_2[i].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         for previous_const, value in result_arg_1[j].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         result.append(result_temp)      
     # elif(symbol == 'extract'):
     #      # extract_flag = True
     #      for i in range(len(result_arg)):
     #                result[i] = result_arg[i]
                    
     elif(symbol == 'bvand'):
          random_key_1 = random.choice(list(result_arg_1[0]["result"].keys()))
          random_key_2 = random.choice(list(result_arg_2[0]["result"].keys()))
          ## Having const
          if('const' in result_arg_1[0]["result"][random_key_1]):
               assert len(result_arg_1) == 1
               
               width = len(result_arg_2[0]["result"][random_key_2])
               assert width in cand_masking
               candidate = cand_masking[width]
               for cand in candidate:
                    new_result_temp = {}
                    for i in range(len(result_arg_1[0]["result"])):
                         new_result_temp[i] = cand
                    result_expand.append(new_result_temp)
               
               for i in range(len(result_expand)):
                    for j in range(len(result_arg_2)):
                         assert len(result_expand[i]) == len(result_arg_2[j]["result"])
                         temp_dict = {}
                         result_temp = {}
                         for k in range(len(result_expand[i])):
                              temp_dict[k] = bitwise_and(result_expand[i][k], result_arg_2[j]["result"][k], bit_width=None) 
                         result_temp["result"] = temp_dict
                         result_temp[result_arg_1[0]["result"][random_key_1]] = result_expand[i]
                    
                         for previous_const, value in result_arg_2[j].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         result.append(result_temp) 
          
          elif('const' in result_arg_2[0]["result"][random_key_2]):
               assert len(result_arg_2) == 1
               width = len(result_arg_1[0]["result"][random_key_2])
               if(width in cand_masking):
                    candidate = cand_masking[width]
               else:
                    assert width == 1
                    candidate = ['0','1']
               
               for cand in candidate:
                    new_result_temp = {}
                    for i in range(len(result_arg_2[0]["result"])):
                         new_result_temp[i] = cand
                    result_expand.append(new_result_temp)
               
               for i in range(len(result_expand)):
                    for j in range(len(result_arg_1)):
                         assert len(result_expand[i]) == len(result_arg_1[j]["result"])
                         temp_dict = {}
                         result_temp = {}
                         for k in range(len(result_expand[i])):
                              temp_dict[k] = bitwise_and(result_arg_1[j]["result"][k], result_expand[i][k], bit_width=None) 
                         result_temp["result"] = temp_dict
                         result_temp[result_arg_2[0]["result"][random_key_1]] = result_expand[i]
                    
                         for previous_const, value in result_arg_1[j].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         result.append(result_temp)          
          else:
               for i in range(len(result_arg_2)):
                    for j in range(len(result_arg_1)):
                         assert len(result_arg_2[i]["result"]) == len(result_arg_1[j]["result"])
                         temp_dict = {}
                         result_temp = {}
                         for k in range(len(result_arg_2[i]["result"])):
                              temp_dict[k] = bitwise_and(result_arg_1[j]["result"][k], result_arg_2[i]["result"][k], bit_width=None)
                         result_temp["result"] = temp_dict
                         for previous_const, value in result_arg_2[i].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         for previous_const, value in result_arg_1[j].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         result.append(result_temp)       
     
     elif(symbol == 'bvor'):
          random_key_1 = random.choice(list(result_arg_1[0]["result"].keys()))
          random_key_2 = random.choice(list(result_arg_2[0]["result"].keys()))
          ## Having const
          if('const' in result_arg_1[0]["result"][random_key_1]):
               assert len(result_arg_1) == 1
               
               width = len(result_arg_2[0]["result"][random_key_2])
               assert width in cand_masking
               candidate = cand_masking[width]
               for cand in candidate:
                    new_result_temp = {}
                    for i in range(len(result_arg_1[0]["result"])):
                         new_result_temp[i] = cand
                    result_expand.append(new_result_temp)
               
               for i in range(len(result_expand)):
                    for j in range(len(result_arg_2)):
                         assert len(result_expand[i]) == len(result_arg_2[j]["result"])
                         temp_dict = {}
                         result_temp = {}
                         for k in range(len(result_expand[i])):
                              temp_dict[k] = bitwise_or(result_expand[i][k], result_arg_2[j]["result"][k], bit_width=None) 
                         result_temp["result"] = temp_dict
                         result_temp[result_arg_1[0]["result"][random_key_1]] = result_expand[i]
                    
                         for previous_const, value in result_arg_2[j].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         result.append(result_temp) 
          
          elif('const' in result_arg_2[0]["result"][random_key_2]):
               assert len(result_arg_2) == 1
               width = len(result_arg_1[0]["result"][random_key_2])
               if(width in cand_masking):
                    candidate = cand_masking[width]
               else:
                    assert width == 1
                    candidate = ['0','1']
               
               for cand in candidate:
                    new_result_temp = {}
                    for i in range(len(result_arg_2[0]["result"])):
                         new_result_temp[i] = cand
                    result_expand.append(new_result_temp)
               
               for i in range(len(result_expand)):
                    for j in range(len(result_arg_1)):
                         assert len(result_expand[i]) == len(result_arg_1[j]["result"])
                         temp_dict = {}
                         result_temp = {}
                         for k in range(len(result_expand[i])):
                              temp_dict[k] = bitwise_or(result_arg_1[j]["result"][k], result_expand[i][k], bit_width=None) 
                         result_temp["result"] = temp_dict
                         result_temp[result_arg_2[0]["result"][random_key_1]] = result_expand[i]
                    
                         for previous_const, value in result_arg_1[j].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         result.append(result_temp)          
          else:
               for i in range(len(result_arg_2)):
                    for j in range(len(result_arg_1)):
                         assert len(result_arg_2[i]["result"]) == len(result_arg_1[j]["result"])
                         temp_dict = {}
                         result_temp = {}
                         for k in range(len(result_arg_2[i]["result"])):
                              temp_dict[k] = bitwise_or(result_arg_1[j]["result"][k], result_arg_2[i]["result"][k], bit_width=None)
                         result_temp["result"] = temp_dict
                         for previous_const, value in result_arg_2[i].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         for previous_const, value in result_arg_1[j].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         result.append(result_temp) 
     
     elif(symbol == 'bvsub'):
          random_key_1 = random.choice(list(result_arg_1[0]["result"].keys()))
          random_key_2 = random.choice(list(result_arg_2[0]["result"].keys()))
          ## Having const
          if('const' in result_arg_1[0]["result"][random_key_1]):
               assert len(result_arg_1) == 1
               
               width = len(result_arg_2[0]["result"][random_key_2])
               if(width in cand_const_sub):
                    candidate = cand_const_sub[width]
               else:
                    assert width == 1
                    candidate = ['0','1']
               
               for cand in candidate:
                    new_result_temp = {}
                    for i in range(len(result_arg_1[0]["result"])):
                         new_result_temp[i] = cand
                    result_expand.append(new_result_temp)
               
               for i in range(len(result_expand)):
                    for j in range(len(result_arg_2)):
                         assert len(result_expand[i]) == len(result_arg_2[j]["result"])
                         temp_dict = {}
                         result_temp = {}
                         for k in range(len(result_expand[i])):
                              temp_dict[k] = bitwise_subtraction(result_expand[i][k], result_arg_2[j]["result"][k], bit_width=None) 
                         result_temp["result"] = temp_dict
                         result_temp[result_arg_1[0]["result"][random_key_1]] = result_expand[i]
                    
                         for previous_const, value in result_arg_2[j].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         result.append(result_temp) 
          
          elif('const' in result_arg_2[0]["result"][random_key_2]):
               assert len(result_arg_2) == 1
               width = len(result_arg_1[0]["result"][random_key_2])
               if(width in cand_const_sub):
                    candidate = cand_const_sub[width]
               else:
                    assert width == 1
                    candidate = ['0','1']
               
               for cand in candidate:
                    new_result_temp = {}
                    for i in range(len(result_arg_2[0]["result"])):
                         new_result_temp[i] = cand
                    result_expand.append(new_result_temp)
               
               for i in range(len(result_expand)):
                    for j in range(len(result_arg_1)):
                         assert len(result_expand[i]) == len(result_arg_1[j]["result"])
                         temp_dict = {}
                         result_temp = {}
                         for k in range(len(result_expand[i])):
                              temp_dict[k] = bitwise_subtraction(result_arg_1[j]["result"][k], result_expand[i][k], bit_width=None) 
                         result_temp["result"] = temp_dict
                         result_temp[result_arg_2[0]["result"][random_key_1]] = result_expand[i]
                    
                         for previous_const, value in result_arg_1[j].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         result.append(result_temp)          
          else:
               for i in range(len(result_arg_2)):
                    for j in range(len(result_arg_1)):
                         assert len(result_arg_2[i]["result"]) == len(result_arg_1[j]["result"])
                         temp_dict = {}
                         result_temp = {}
                         for k in range(len(result_arg_2[i]["result"])):
                              temp_dict[k] = bitwise_subtraction(result_arg_1[j]["result"][k], result_arg_2[i]["result"][k], bit_width=None)
                         result_temp["result"] = temp_dict
                         for previous_const, value in result_arg_2[i].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         for previous_const, value in result_arg_1[j].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         result.append(result_temp) 
     
     elif(symbol == 'bvadd'):          
          random_key_1 = random.choice(list(result_arg_1[0]["result"].keys()))
          random_key_2 = random.choice(list(result_arg_2[0]["result"].keys()))
          if('const' in result_arg_1[0]["result"][random_key_1]):
               assert len(result_arg_1) == 1
               
               width = len(result_arg_2[0]["result"][random_key_2])
               if(width in cand_const_add):
                    candidate = cand_const_add[width]
               else:
                    assert width == 1
                    candidate = ['0','1']
               for cand in candidate:
                    new_result_temp = {}
                    for i in range(len(result_arg_1[0]["result"])):
                         new_result_temp[i] = cand
                    result_expand.append(new_result_temp)
               
               for i in range(len(result_expand)):
                    for j in range(len(result_arg_2)):
                         assert len(result_expand[i]) == len(result_arg_2[j]["result"])
                         temp_dict = {}
                         result_temp = {}
                         for k in range(len(result_expand[i])):
                              temp_dict[k] = bitwise_addition(result_expand[i][k], result_arg_2[j]["result"][k], bit_width=None) 
                         result_temp["result"] = temp_dict
                         result_temp[result_arg_1[0]["result"][random_key_1]] = result_expand[i]
                    
                         for previous_const, value in result_arg_2[j].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         result.append(result_temp) 
          
          elif('const' in result_arg_2[0]["result"][random_key_2]):
               assert len(result_arg_2) == 1
               width = len(result_arg_1[0]["result"][random_key_2])
               if(width in cand_const_add):
                    candidate = cand_const_add[width]
               else:
                    assert width == 1
                    candidate = ['0','1']
               
               for cand in candidate:
                    new_result_temp = {}
                    for i in range(len(result_arg_2[0]["result"])):
                         new_result_temp[i] = cand
                    result_expand.append(new_result_temp)
               
               for i in range(len(result_expand)):
                    for j in range(len(result_arg_1)):
                         assert len(result_expand[i]) == len(result_arg_1[j]["result"])
                         temp_dict = {}
                         result_temp = {}
                         for k in range(len(result_expand[i])):
                              temp_dict[k] = bitwise_addition(result_expand[i][k], result_arg_1[j]["result"][k], bit_width=None) 
                         result_temp["result"] = temp_dict
                         result_temp[result_arg_2[0]["result"][random_key_1]] = result_expand[i]
                    
                         for previous_const, value in result_arg_1[j].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         result.append(result_temp)          
          else:
               for i in range(len(result_arg_2)):
                    for j in range(len(result_arg_1)):
                         assert len(result_arg_2[i]["result"]) == len(result_arg_1[j]["result"])
                         temp_dict = {}
                         result_temp = {}
                         for k in range(len(result_arg_2[i]["result"])):
                              temp_dict[k] = bitwise_addition(result_arg_2[i]["result"][k], result_arg_1[j]["result"][k], bit_width=None)
                         result_temp["result"] = temp_dict
                         for previous_const, value in result_arg_2[i].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         for previous_const, value in result_arg_1[j].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         result.append(result_temp) 
     
     elif(symbol == 'bvxor'):
          random_key_1 = random.choice(list(result_arg_1[0]["result"].keys()))
          random_key_2 = random.choice(list(result_arg_2[0]["result"].keys()))
          ## Having const
          if('const' in result_arg_1[0]["result"][random_key_1]):
               assert len(result_arg_1) == 1
               
               width = len(result_arg_2[0]["result"][random_key_2])
               assert width in cand_masking
               candidate = cand_masking[width]
               for cand in candidate:
                    new_result_temp = {}
                    for i in range(len(result_arg_1[0]["result"])):
                         new_result_temp[i] = cand
                    result_expand.append(new_result_temp)
               
               for i in range(len(result_expand)):
                    for j in range(len(result_arg_2)):
                         assert len(result_expand[i]) == len(result_arg_2[j]["result"])
                         temp_dict = {}
                         result_temp = {}
                         for k in range(len(result_expand[i])):
                              temp_dict[k] = bitwise_xor(result_expand[i][k], result_arg_2[j]["result"][k], bit_width=None) 
                         result_temp["result"] = temp_dict
                         result_temp[result_arg_1[0]["result"][random_key_1]] = result_expand[i]
                    
                         for previous_const, value in result_arg_2[j].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         result.append(result_temp) 
          
          elif('const' in result_arg_2[0]["result"][random_key_2]):
               assert len(result_arg_2) == 1
               width = len(result_arg_1[0]["result"][random_key_2])
               if(width in cand_masking):
                    candidate = cand_masking[width]
               else:
                    assert width == 1
                    candidate = ['0','1']
               
               for cand in candidate:
                    new_result_temp = {}
                    for i in range(len(result_arg_2[0]["result"])):
                         new_result_temp[i] = cand
                    result_expand.append(new_result_temp)
               
               for i in range(len(result_expand)):
                    for j in range(len(result_arg_1)):
                         assert len(result_expand[i]) == len(result_arg_1[j]["result"])
                         temp_dict = {}
                         result_temp = {}
                         for k in range(len(result_expand[i])):
                              temp_dict[k] = bitwise_xor(result_arg_1[j]["result"][k], result_expand[i][k], bit_width=None) 
                         result_temp["result"] = temp_dict
                         result_temp[result_arg_2[0]["result"][random_key_1]] = result_expand[i]
                    
                         for previous_const, value in result_arg_1[j].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         result.append(result_temp)          
          else:
               for i in range(len(result_arg_2)):
                    for j in range(len(result_arg_1)):
                         assert len(result_arg_2[i]["result"]) == len(result_arg_1[j]["result"])
                         temp_dict = {}
                         result_temp = {}
                         for k in range(len(result_arg_2[i]["result"])):
                              temp_dict[k] = bitwise_xor(result_arg_1[j]["result"][k], result_arg_2[i]["result"][k], bit_width=None)
                         result_temp["result"] = temp_dict
                         for previous_const, value in result_arg_2[i].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         for previous_const, value in result_arg_1[j].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         result.append(result_temp)   

     assert (len(result)!=0)
     return result

def recursive_calculation_random(dic_value, pg, generate_tree, cand_const_add, cand_const_sub,cand_masking):

     symbol = generate_tree.app
     result = []
     result_expand = []
     # extract_flag = False
     if(is_terminal(pg,symbol)):
          result_dict = {}
          result_temp = {}
          if('const' in symbol):
               random_key = random.choice(list(dic_value.keys()))
               for i in range(len(dic_value[random_key])):
                    result_temp[i] = symbol
          else:
               for i in range(len(dic_value[symbol])):
                    result_temp[i] = dic_value[symbol][i]
          result_dict["result"] = result_temp
          return [result_dict]

     if(len(generate_tree.args)==2):
          result_arg_1 = recursive_calculation_random( dic_value, pg, generate_tree.args[0], cand_const_add, cand_const_sub,cand_masking)
          result_arg_2 = recursive_calculation_random( dic_value, pg, generate_tree.args[1], cand_const_add, cand_const_sub,cand_masking)
          # assert len(result_arg_1) == len(result_arg_2) 
     
     if(symbol == 'eq'):
          random_key_1 = random.choice(list(result_arg_1[0]["result"].keys()))
          random_key_2 = random.choice(list(result_arg_2[0]["result"].keys()))
          ## Having const
          # const_candidate = []
          if('const' in result_arg_1[0]["result"][random_key_1] and 'const' in result_arg_2[0]["result"][random_key_2]):
               assert len(result_arg_1) == 1
               assert len(result_arg_2) == 1
               temp_dict = {}
               result_temp = {}  
               for k in range(len(result_arg_1[0]["result"])):
                    temp_dict[k] = result_arg_1[0]["result"][k]
               result_temp["result"] = temp_dict
               result.append(result_temp) 
          
          elif('const' in result_arg_1[0]["result"][random_key_1]):
               assert len(result_arg_1) == 1
               for j in range(len(result_arg_2)):
                    result_expand = []
                    if (result_arg_2[0]["result"][random_key_2]=='-1'):
                         width = 1
                    else:
                         width = len(result_arg_2[0]["result"][random_key_2])
                    random_binary_string = ''.join(random.choice(['0', '1']) for _ in range(width))
                    new_result_temp = {}
                    for i in range(len(result_arg_1[0]["result"])):
                         new_result_temp[i] = random_binary_string
                    result_expand.append(new_result_temp)
                    
                    for i in range(len(result_expand)):
                         # for j in range(len(result_arg_2)):
                              assert len(result_expand[i]) == len(result_arg_2[j]["result"])
                              temp_dict = {}
                              result_temp = {}
                              for k in range(len(result_expand[i])):
                                   if((len(result_expand[i][k]) != len(result_arg_2[j]["result"][k])) or (result_arg_2[j]["result"][k])=='-1'):
                                        temp_dict[k] = '-1'
                                   elif(result_expand[i][k]==result_arg_2[j]["result"][k]):
                                        temp_dict[k] = '1' 
                                   else:
                                        temp_dict[k] = '0'
                              result_temp["result"] = temp_dict
                              result_temp[result_arg_1[0]["result"][random_key_1]] = result_expand[i]
                         
                              for previous_const, value in result_arg_2[j].items():
                                   if previous_const == "result":
                                        continue
                                   result_temp[previous_const] = value
                              result.append(result_temp) 
          
          elif('const' in result_arg_2[0]["result"][random_key_2]):
               assert len(result_arg_2) == 1
               for j in range(len(result_arg_1)):
                    # const_candidate = list(set(candidate + const_candidate))
                    result_expand = []
                    if(result_arg_1[0]["result"][random_key_1]=='-1'):
                         width = 1
                    else:
                         width = len(result_arg_1[0]["result"][random_key_1])
                    random_binary_string = ''.join(random.choice(['0', '1']) for _ in range(width))
                    new_result_temp = {}
                    for i in range(len(result_arg_2[0]["result"])):
                         new_result_temp[i] = random_binary_string
                    result_expand.append(new_result_temp)
                    for i in range(len(result_expand)):
                         # for j in range(len(result_arg_1)):
                              assert len(result_expand[i]) == len(result_arg_1[j]["result"])
                              temp_dict = {}
                              result_temp = {}
                              for k in range(len(result_expand[i])):
                                   if((len(result_expand[i][k]) != len(result_arg_1[j]["result"][k])) or (result_arg_1[j]["result"][k]=='-1')):
                                        temp_dict[k] = '-1'
                                   elif(result_expand[i][k]==result_arg_1[j]["result"][k]):
                                        temp_dict[k] = '1' 
                                   else:
                                        temp_dict[k] = '0'
                              result_temp["result"] = temp_dict
                              result_temp[result_arg_2[0]["result"][random_key_1]] = result_expand[i]
                         
                              for previous_const, value in result_arg_1[j].items():
                                   if previous_const == "result":
                                        continue
                                   result_temp[previous_const] = value
                              result.append(result_temp)        
          else:
               for i in range(len(result_arg_2)):
                    for j in range(len(result_arg_1)):
                         assert len(result_arg_2[i]["result"]) == len(result_arg_1[j]["result"])
                         temp_dict = {}
                         result_temp = {}
                         for k in range(len(result_arg_2[i]["result"])):
                              if((len(result_arg_2[i]["result"][k]) != len(result_arg_1[j]["result"][k])) or (result_arg_2[i]["result"][k]=='-1')
                                 or (result_arg_1[j]["result"][k]=='-1')):
                                   temp_dict[k] = '-1'
                              elif(result_arg_2[i]["result"][k]==result_arg_1[j]["result"][k]):
                                   temp_dict[k] = '1' 
                              else:
                                   temp_dict[k] = '0'
                         result_temp["result"] = temp_dict
                    
                         for previous_const, value in result_arg_2[i].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         for previous_const, value in result_arg_1[j].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         result.append(result_temp) 

     elif(symbol == 'bvule'):
          random_key_1 = random.choice(list(result_arg_1[0]["result"].keys()))
          random_key_2 = random.choice(list(result_arg_2[0]["result"].keys()))
          # const_candidate = []
          ## Having const
          if('const' in result_arg_1[0]["result"][random_key_1] and 'const' in result_arg_2[0]["result"][random_key_2]):
               assert len(result_arg_1) == 1
               assert len(result_arg_2) == 1
               temp_dict = {}
               result_temp = {}  
               for k in range(len(result_arg_1[0]["result"])):
                    temp_dict[k] = result_arg_1[0]["result"][k]
               result_temp["result"] = temp_dict
               result.append(result_temp) 
          
          elif('const' in result_arg_1[0]["result"][random_key_1]):
               assert len(result_arg_1) == 1
               for j in range(len(result_arg_2)):
                    result_expand = []
                    if(result_arg_2[0]["result"][random_key_2]=='-1'):
                         width = 1
                    else:
                         width = len(result_arg_2[0]["result"][random_key_2])
                    random_binary_string = ''.join(random.choice(['0', '1']) for _ in range(width))
                    new_result_temp = {}
                    for i in range(len(result_arg_1[0]["result"])):
                         new_result_temp[i] = random_binary_string
                    result_expand.append(new_result_temp)
                    
                    for i in range(len(result_expand)):
                         # for j in range(len(result_arg_2)):
                              assert len(result_expand[i]) == len(result_arg_2[j]["result"])
                              temp_dict = {}
                              result_temp = {}
                              for k in range(len(result_expand[i])):
                                   if((len(result_expand[i][k]) != len(result_arg_2[j]["result"][k])) or (result_arg_2[j]["result"][k]=='-1')):
                                        temp_dict[k] = '-1'
                                   elif(result_expand[i][k]<=result_arg_2[j]["result"][k]):
                                        temp_dict[k] = '1' 
                                   else:
                                        temp_dict[k] = '0'
                              result_temp["result"] = temp_dict
                              result_temp[result_arg_1[0]["result"][random_key_1]] = result_expand[i]
                         
                              for previous_const, value in result_arg_2[j].items():
                                   if previous_const == "result":
                                        continue
                                   result_temp[previous_const] = value
                              result.append(result_temp) 
          
          elif('const' in result_arg_2[0]["result"][random_key_2]):
               assert len(result_arg_2) == 1
               for j in range(len(result_arg_1)):
                    # const_candidate = list(set(candidate + const_candidate))
                    result_expand = []
                    if result_arg_1[0]["result"][random_key_1] == '-1':
                         width = 1
                    else:
                         width = len(result_arg_1[0]["result"][random_key_1])
                    random_binary_string = ''.join(random.choice(['0', '1']) for _ in range(width))
                    new_result_temp = {}
                    for i in range(len(result_arg_2[0]["result"])):
                         new_result_temp[i] = random_binary_string
                    result_expand.append(new_result_temp)
                    for i in range(len(result_expand)):
                         # for j in range(len(result_arg_1)):
                              assert len(result_expand[i]) == len(result_arg_1[j]["result"])
                              temp_dict = {}
                              result_temp = {}
                              for k in range(len(result_expand[i])):
                                   if((len(result_expand[i][k]) != len(result_arg_1[j]["result"][k])) or (result_arg_1[j]["result"][k]=='-1')):
                                        temp_dict[k] = '-1'
                                   elif(result_expand[i][k]<=result_arg_1[j]["result"][k]):
                                        temp_dict[k] = '1' 
                                   else:
                                        temp_dict[k] = '0'
                              result_temp["result"] = temp_dict
                              result_temp[result_arg_2[0]["result"][random_key_1]] = result_expand[i]
                         
                              for previous_const, value in result_arg_1[j].items():
                                   if previous_const == "result":
                                        continue
                                   result_temp[previous_const] = value
                              result.append(result_temp)           
          else:
               for i in range(len(result_arg_2)):
                    for j in range(len(result_arg_1)):
                         assert len(result_arg_2[i]["result"]) == len(result_arg_1[j]["result"])
                         temp_dict = {}
                         result_temp = {}

                         for k in range(len(result_arg_2[i]["result"])):
                              if((len(result_arg_2[i]["result"][k])!=len(result_arg_1[j]["result"][k])) or (result_arg_2[i]["result"][k]=='-1')
                                   or (result_arg_1[j]["result"][k]== '-1')):
                                   temp_dict[k] = '-1'
                              elif(int(result_arg_2[i]["result"][k],2)>=int(result_arg_1[j]["result"][k],2)):
                                   temp_dict[k] = '1' 
                              else:
                                   temp_dict[k] = '0'
                         result_temp["result"] = temp_dict
                         for previous_const, value in result_arg_2[i].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         for previous_const, value in result_arg_1[j].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         result.append(result_temp) 



     #      # extract_flag = True
     #      for i in range(len(result_arg)):
     #                result[i] = result_arg[i]
                    
     elif(symbol == 'bvand'):
          random_key_1 = random.choice(list(result_arg_1[0]["result"].keys()))
          random_key_2 = random.choice(list(result_arg_2[0]["result"].keys()))
          ## Having const
          if('const' in result_arg_1[0]["result"][random_key_1] and 'const' in result_arg_2[0]["result"][random_key_2]):
               assert len(result_arg_1) == 1
               assert len(result_arg_2) == 1
               temp_dict = {}
               result_temp = {}  
               for k in range(len(result_arg_1[0]["result"])):
                    temp_dict[k] = result_arg_1[0]["result"][k]
               result_temp["result"] = temp_dict
               result.append(result_temp) 
          
          elif('const' in result_arg_1[0]["result"][random_key_1]):
               assert len(result_arg_1) == 1
               if(result_arg_2[0]["result"][random_key_2]=='-1'):
                    width = 1
               else:
                    width = len(result_arg_2[0]["result"][random_key_2])
               random_binary_string = ''.join(random.choice(['0', '1']) for _ in range(width))
               # candidate = cand_masking[width]
               # for cand in candidate:
               new_result_temp = {}
               for i in range(len(result_arg_1[0]["result"])):
                    new_result_temp[i] = random_binary_string
               result_expand.append(new_result_temp)
               
               for i in range(len(result_expand)):
                    for j in range(len(result_arg_2)):
                         assert len(result_expand[i]) == len(result_arg_2[j]["result"])
                         temp_dict = {}
                         result_temp = {}
                         for k in range(len(result_expand[i])):
                              if((result_expand[i][k]!=result_arg_2[j]["result"][k]) or (result_arg_2[j]["result"][k]=='-1')):
                                   temp_dict[k] = '-1'
                              else:
                                   temp_dict[k] = bitwise_and(result_expand[i][k], result_arg_2[j]["result"][k], bit_width=None) 
                         result_temp["result"] = temp_dict
                         result_temp[result_arg_1[0]["result"][random_key_1]] = result_expand[i]
                    
                         for previous_const, value in result_arg_2[j].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         result.append(result_temp) 
          
          elif('const' in result_arg_2[0]["result"][random_key_2]):
               assert len(result_arg_2) == 1
               if(result_arg_1[0]["result"][random_key_2]=='-1'):
                    width = 1
               else:
                    width = len(result_arg_1[0]["result"][random_key_2])
               random_binary_string = ''.join(random.choice(['0', '1']) for _ in range(width))
               # candidate = cand_masking[width]
               # for cand in candidate:
               new_result_temp = {}
               for i in range(len(result_arg_2[0]["result"])):
                    new_result_temp[i] = random_binary_string
               result_expand.append(new_result_temp)
               
               for i in range(len(result_expand)):
                    for j in range(len(result_arg_1)):
                         assert len(result_expand[i]) == len(result_arg_1[j]["result"])
                         temp_dict = {}
                         result_temp = {}
                         for k in range(len(result_expand[i])):
                              if((len(result_expand[i][k]) != len(result_arg_1[j]["result"][k])) or (result_arg_1[j]["result"][k]=='-1')):
                                   temp_dict[k] = '-1'
                              else:
                                   temp_dict[k] = bitwise_and(result_arg_1[j]["result"][k], result_expand[i][k], bit_width=None) 
                         result_temp["result"] = temp_dict
                         result_temp[result_arg_2[0]["result"][random_key_1]] = result_expand[i]
                    
                         for previous_const, value in result_arg_1[j].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         result.append(result_temp)          
          else:
               for i in range(len(result_arg_2)):
                    for j in range(len(result_arg_1)):
                         assert len(result_arg_2[i]["result"]) == len(result_arg_1[j]["result"])
                         temp_dict = {}
                         result_temp = {}
                         for k in range(len(result_arg_2[i]["result"])):
                              if((len(result_arg_2[i]["result"][k]) != len(result_arg_1[j]["result"][k])) or (result_arg_2[i]["result"][k]=='-1')
                                 or (result_arg_1[j]["result"][k]=='-1')):
                                   temp_dict[k] = '-1'
                              else:
                                   temp_dict[k] = bitwise_and(result_arg_1[j]["result"][k], result_arg_2[i]["result"][k], bit_width=None)

                         result_temp["result"] = temp_dict
                         for previous_const, value in result_arg_2[i].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         for previous_const, value in result_arg_1[j].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         result.append(result_temp)       
     
     elif(symbol == 'bvor'):
          random_key_1 = random.choice(list(result_arg_1[0]["result"].keys()))
          random_key_2 = random.choice(list(result_arg_2[0]["result"].keys()))
          ## Having const
          if('const' in result_arg_1[0]["result"][random_key_1] and 'const' in result_arg_2[0]["result"][random_key_2]):
               assert len(result_arg_1) == 1
               assert len(result_arg_2) == 1
               temp_dict = {}
               result_temp = {}  
               for k in range(len(result_arg_1[0]["result"])):
                    temp_dict[k] = result_arg_1[0]["result"][k]
               result_temp["result"] = temp_dict
               result.append(result_temp) 
          elif('const' in result_arg_1[0]["result"][random_key_1]):
               assert len(result_arg_1) == 1
               if(result_arg_2[0]["result"][random_key_2]):
                    width = 1
               else:
                    width = len(result_arg_2[0]["result"][random_key_2])
               # assert width in cand_masking
               random_binary_string = ''.join(random.choice(['0', '1']) for _ in range(width))
               # candidate = cand_masking[width]
               # for cand in candidate:
               new_result_temp = {}
               for i in range(len(result_arg_1[0]["result"])):
                    new_result_temp[i] = random_binary_string
               result_expand.append(new_result_temp)
               
               for i in range(len(result_expand)):
                    for j in range(len(result_arg_2)):
                         assert len(result_expand[i]) == len(result_arg_2[j]["result"])
                         temp_dict = {}
                         result_temp = {}
                         for k in range(len(result_expand[i])):
                              if((len(result_expand[i][k]) != len(result_arg_2[j]["result"][k])) or (result_arg_2[j]["result"][k]=='-1')):
                                   temp_dict[k] = '-1'
                              else:
                                   temp_dict[k] = bitwise_or(result_expand[i][k], result_arg_2[j]["result"][k], bit_width=None) 
                         result_temp["result"] = temp_dict
                         result_temp[result_arg_1[0]["result"][random_key_1]] = result_expand[i]
                    
                         for previous_const, value in result_arg_2[j].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         result.append(result_temp) 
          
          elif('const' in result_arg_2[0]["result"][random_key_2]):
               assert len(result_arg_2) == 1
               if(result_arg_1[0]["result"][random_key_2]=='-1'):
                    width = 1 
               else:
                    width = len(result_arg_1[0]["result"][random_key_2])
               random_binary_string = ''.join(random.choice(['0', '1']) for _ in range(width))
               # candidate = cand_masking[width]
               # for cand in candidate:
               new_result_temp = {}
               for i in range(len(result_arg_2[0]["result"])):
                    new_result_temp[i] = random_binary_string
               result_expand.append(new_result_temp)
               
               for i in range(len(result_expand)):
                    for j in range(len(result_arg_1)):
                         assert len(result_expand[i]) == len(result_arg_1[j]["result"])
                         temp_dict = {}
                         result_temp = {}
                         for k in range(len(result_expand[i])):
                              if((len(result_expand[i][k]) != len(result_arg_1[j]["result"][k])) or (result_arg_1[j]["result"][k]!='-1')):
                                   temp_dict[k] = '-1'
                              else:
                                   temp_dict[k] = bitwise_or(result_arg_1[j]["result"][k], result_expand[i][k], bit_width=None) 
                         result_temp["result"] = temp_dict
                         result_temp[result_arg_2[0]["result"][random_key_1]] = result_expand[i]
                    
                         for previous_const, value in result_arg_1[j].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         result.append(result_temp)          
          else:
               for i in range(len(result_arg_2)):
                    for j in range(len(result_arg_1)):
                         assert len(result_arg_2[i]["result"]) == len(result_arg_1[j]["result"])
                         temp_dict = {}
                         result_temp = {}
                         for k in range(len(result_arg_2[i]["result"])):
                              if((len(result_arg_2[i]["result"][k]) != len(result_arg_1[j]["result"][k])) or (result_arg_2[i]["result"][k]=='-1')
                                 or (result_arg_1[j]["result"][k]=='-1')):
                                   temp_dict[k] = '-1'
                              else:
                                   temp_dict[k] = bitwise_or(result_arg_1[j]["result"][k], result_arg_2[i]["result"][k], bit_width=None)
                         result_temp["result"] = temp_dict
                         for previous_const, value in result_arg_2[i].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         for previous_const, value in result_arg_1[j].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         result.append(result_temp) 
     
     elif(symbol == 'bvsub'):
          random_key_1 = random.choice(list(result_arg_1[0]["result"].keys()))
          random_key_2 = random.choice(list(result_arg_2[0]["result"].keys()))
          ## Having const
          if('const' in result_arg_1[0]["result"][random_key_1] and 'const' in result_arg_2[0]["result"][random_key_2]):
               assert len(result_arg_1) == 1
               assert len(result_arg_2) == 1
               temp_dict = {}
               result_temp = {}  
               for k in range(len(result_arg_1[0]["result"])):
                    temp_dict[k] = result_arg_1[0]["result"][k]
               result_temp["result"] = temp_dict
               result.append(result_temp) 

          elif('const' in result_arg_1[0]["result"][random_key_1]):
               assert len(result_arg_1) == 1
               if(result_arg_2[0]["result"][random_key_2]=='-1'):
                    width = 1
               else:
                    width = len(result_arg_2[0]["result"][random_key_2])
               random_binary_string = ''.join(random.choice(['0', '1']) for _ in range(width))
               # candidate = cand_masking[width]
               # for cand in candidate:
               new_result_temp = {}
               for i in range(len(result_arg_1[0]["result"])):
                    new_result_temp[i] = random_binary_string
               result_expand.append(new_result_temp)
               
               for i in range(len(result_expand)):
                    for j in range(len(result_arg_2)):
                         assert len(result_expand[i]) == len(result_arg_2[j]["result"])
                         temp_dict = {}
                         result_temp = {}
                         for k in range(len(result_expand[i])):
                              if(len(result_expand[i][k]) != len(result_arg_2[j]["result"][k]) or (result_arg_2[j]["result"][k]=='-1')):
                                   temp_dict[k] = '-1'
                              else:
                                   temp_dict[k] = bitwise_subtraction(result_expand[i][k], result_arg_2[j]["result"][k], bit_width=None) 
                         result_temp["result"] = temp_dict
                         result_temp[result_arg_1[0]["result"][random_key_1]] = result_expand[i]
                    
                         for previous_const, value in result_arg_2[j].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         result.append(result_temp) 
          
          elif('const' in result_arg_2[0]["result"][random_key_2]):
               assert len(result_arg_2) == 1
               if(result_arg_1[0]["result"][random_key_2]=='-1'):
                    width = 1
               else:
                    width = len(result_arg_1[0]["result"][random_key_2])
               random_binary_string = ''.join(random.choice(['0', '1']) for _ in range(width))
               # candidate = cand_masking[width]
               # for cand in candidate:
               new_result_temp = {}
               for i in range(len(result_arg_2[0]["result"])):
                    new_result_temp[i] = random_binary_string
               result_expand.append(new_result_temp)
               
               for i in range(len(result_expand)):
                    for j in range(len(result_arg_1)):
                         assert len(result_expand[i]) == len(result_arg_1[j]["result"])
                         temp_dict = {}
                         result_temp = {}
                         for k in range(len(result_expand[i])):
                              if((len(result_expand[i][k]) != len(result_arg_1[j]["result"][k])) or (result_arg_1[j]["result"][k]=='-1')):
                                   temp_dict[k] = '-1'
                              else:
                                   temp_dict[k] = bitwise_subtraction(result_arg_1[j]["result"][k], result_expand[i][k], bit_width=None) 
                         result_temp["result"] = temp_dict
                         result_temp[result_arg_2[0]["result"][random_key_1]] = result_expand[i]
                    
                         for previous_const, value in result_arg_1[j].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         result.append(result_temp)          
          else:
               for i in range(len(result_arg_2)):
                    for j in range(len(result_arg_1)):
                         assert len(result_arg_2[i]["result"]) == len(result_arg_1[j]["result"])
                         temp_dict = {}
                         result_temp = {}
                         for k in range(len(result_arg_2[i]["result"])):
                              if((len(result_arg_2[i]["result"][k]) != len(result_arg_1[j]["result"][k])) or (result_arg_2[i]["result"][k]=='-1')
                                 or (result_arg_1[j]["result"][k]=='-1')):
                                   temp_dict[k] = '-1'
                              else:
                                   temp_dict[k] = bitwise_subtraction(result_arg_1[j]["result"][k], result_arg_2[i]["result"][k], bit_width=None)
                         result_temp["result"] = temp_dict
                         for previous_const, value in result_arg_2[i].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         for previous_const, value in result_arg_1[j].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         result.append(result_temp) 
     
     elif(symbol == 'bvadd'):          
          random_key_1 = random.choice(list(result_arg_1[0]["result"].keys()))
          random_key_2 = random.choice(list(result_arg_2[0]["result"].keys()))
          if('const' in result_arg_1[0]["result"][random_key_1] and 'const' in result_arg_2[0]["result"][random_key_2]):
               assert len(result_arg_1) == 1
               assert len(result_arg_2) == 1
               temp_dict = {}
               result_temp = {}  
               for k in range(len(result_arg_1[0]["result"])):
                    temp_dict[k] = result_arg_1[0]["result"][k]
               result_temp["result"] = temp_dict
               result.append(result_temp) 
          elif('const' in result_arg_1[0]["result"][random_key_1]):
               assert len(result_arg_1) == 1
               if(result_arg_2[0]["result"][random_key_2]=='-1'):
                    width = 1
               else:
                    width = len(result_arg_2[0]["result"][random_key_2])
               random_binary_string = ''.join(random.choice(['0', '1']) for _ in range(width))
               # candidate = cand_masking[width]
               # for cand in candidate:
               new_result_temp = {}
               for i in range(len(result_arg_1[0]["result"])):
                    new_result_temp[i] = random_binary_string
               result_expand.append(new_result_temp)
               
               for i in range(len(result_expand)):
                    for j in range(len(result_arg_2)):
                         assert len(result_expand[i]) == len(result_arg_2[j]["result"])
                         temp_dict = {}
                         result_temp = {}
                         for k in range(len(result_expand[i])):
                              if((len(result_expand[i][k]) != len(result_arg_2[j]["result"][k])) or (result_arg_2[j]["result"][k]=='-1')):
                                   temp_dict[k] = '-1'
                              else:
                                   temp_dict[k] = bitwise_addition(result_expand[i][k], result_arg_2[j]["result"][k], bit_width=None) 
                         result_temp["result"] = temp_dict
                         result_temp[result_arg_1[0]["result"][random_key_1]] = result_expand[i]
                    
                         for previous_const, value in result_arg_2[j].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         result.append(result_temp) 
          
          elif('const' in result_arg_2[0]["result"][random_key_2]):
               assert len(result_arg_2) == 1
               if(result_arg_1[0]["result"][random_key_2]=='-1'):
                    width = 1
               else: 
                    width = len(result_arg_1[0]["result"][random_key_2])
               random_binary_string = ''.join(random.choice(['0', '1']) for _ in range(width))
               # candidate = cand_masking[width]
               # for cand in candidate:
               new_result_temp = {}
               for i in range(len(result_arg_2[0]["result"])):
                    new_result_temp[i] = random_binary_string
               result_expand.append(new_result_temp)
               
               for i in range(len(result_expand)):
                    for j in range(len(result_arg_1)):
                         assert len(result_expand[i]) == len(result_arg_1[j]["result"])
                         temp_dict = {}
                         result_temp = {}
                         for k in range(len(result_expand[i])):
                              if((len(result_expand[i][k]) != len(result_arg_1[j]["result"][k])) or (result_arg_1[j]["result"][k]=='-1')):
                                   temp_dict[k] = '-1'
                              else:
                                   temp_dict[k] = bitwise_addition(result_expand[i][k], result_arg_1[j]["result"][k], bit_width=None) 
                         result_temp["result"] = temp_dict
                         result_temp[result_arg_2[0]["result"][random_key_1]] = result_expand[i]
                    
                         for previous_const, value in result_arg_1[j].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         result.append(result_temp)          
          else:
               for i in range(len(result_arg_2)):
                    for j in range(len(result_arg_1)):
                         assert len(result_arg_2[i]["result"]) == len(result_arg_1[j]["result"])
                         temp_dict = {}
                         result_temp = {}
                         for k in range(len(result_arg_2[i]["result"])):
                              if((len(result_arg_2[i]["result"][k]) != len(result_arg_1[j]["result"][k])) or (result_arg_2[i]["result"][k]=='-1')
                                 or (result_arg_1[j]["result"][k]=='-1')):
                                   temp_dict[k] = '-1'
                              else:
                                   temp_dict[k] = bitwise_addition(result_arg_2[i]["result"][k], result_arg_1[j]["result"][k], bit_width=None)
                         
                         result_temp["result"] = temp_dict
                         for previous_const, value in result_arg_2[i].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         for previous_const, value in result_arg_1[j].items():
                              if previous_const == "result":
                                   continue
                              result_temp[previous_const] = value
                         result.append(result_temp) 
     

     assert (len(result)!=0)
     return result


def inner_fault_coverage(fault_pattern, pg, generate_tree):
     symbol = generate_tree.app
     result = {}
     if(is_terminal(pg,symbol)):
          # assert len(fault_pattern[symbol]) == 1
          result[0] = fault_pattern[symbol]
          return result

     if(len(generate_tree.args)==2):
          result_arg_1 = inner_fault_coverage( fault_pattern, pg, generate_tree.args[0])
          result_arg_2 = inner_fault_coverage( fault_pattern, pg, generate_tree.args[1])
     
     assert len(result_arg_1) == len(result_arg_2)
     
     
     if(symbol == 'eq'):
          for i in range(len(result_arg_1)):
               # if((result_arg_2[i]=='-1') or (result_arg_1[i]=='-1')):
               #      result[i] = '-1'
               #      continue
               if(result_arg_1[i]==result_arg_2[i]):
                    result[i] = '1' 
               else:
                    result[i] = '0'
     
     # elif(symbol == 'uneq'):
     #      for i in range(len(result_arg_1)):
     #           if((result_arg_2[i]=='-1') or (result_arg_1[i]=='-1')):
     #                result[i] = '-1'
     #                continue
     #           if(result_arg_1[i]!=result_arg_2[i]):
     #                result[i] = '1' 
     #           else:
     #                result[i] = '0'

     elif(symbol == 'bvule'):
          for i in range(len(result_arg_1)):
               if((result_arg_2[i]=='-1') or (result_arg_1[i]=='-1')):
                    result[i] = '-1'
                    continue
               if(result_arg_1[i] <= result_arg_2[i]):
                    result[i] = '1' 
               else:
                    result[i] = '0'

     elif(symbol == 'bvuge'):
          for i in range(len(result_arg_1)):
               if((result_arg_2[i]=='-1') or (result_arg_1[i]=='-1')):
                    result[i] = '-1'
                    continue
               if(result_arg_1[i] >= result_arg_2[i]):
                    result[i] = '1' 
               else:
                    result[i] = '0'

     elif(symbol == 'bvand'):
          for i in range(len(result_arg_2)):
               # if((result_arg_2[i]=='-1') or (result_arg_1[i]=='-1')):
               #      result[i] = '-1'
               #      continue
               result[i] =  bitwise_and(result_arg_1[i], result_arg_2[i], bit_width=None)

     elif(symbol == 'bvor'):
          for i in range(len(result_arg_2)):
               # if((result_arg_2[i]=='-1') or (result_arg_1[i]=='-1')):
               #      result[i] = '-1'
               #      continue
               result[i] =  bitwise_or(result_arg_1[i], result_arg_2[i], bit_width=None)

     elif(symbol == 'bvsub'):
          for i in range(len(result_arg_2)):
               # if((result_arg_2[i]=='-1') or (result_arg_1[i]=='-1')):
               #      result[i] = '-1'
               #      continue
               result[i] = bitwise_subtraction(result_arg_1[i], result_arg_2[i], bit_width=None)
     
     elif(symbol == 'bvadd'):
          for i in range(len(result_arg_2)):
               # if((result_arg_2[i]=='-1') or (result_arg_1[i]=='-1')):
               #      result[i] = '-1'
               #      continue
               result[i] = bitwise_addition(result_arg_1[i], result_arg_2[i], bit_width=None)

     elif(symbol == 'bvxor'):
          for i in range(len(result_arg_2)):
               # if((result_arg_2[i]=='-1') or (result_arg_1[i]=='-1')):
               #      result[i] = '-1'
               #      continue
               result[i] = bitwise_xor(result_arg_1[i], result_arg_2[i], bit_width=None)

     
     return result

def inner_fault_coverage_for_concrete_tree(fault_pattern, pg, generate_tree):
     symbol = generate_tree.app
     result = {}
     if(symbol.isdigit()):
          result[0] = symbol
          return result
     if(is_terminal(pg,symbol)):
          # assert len(fault_pattern[symbol]) == 1
          result[0] = fault_pattern[symbol]
          return result

     if(len(generate_tree.args)==2):
          result_arg_1 = inner_fault_coverage_for_concrete_tree( fault_pattern, pg, generate_tree.args[0])
          result_arg_2 = inner_fault_coverage_for_concrete_tree( fault_pattern, pg, generate_tree.args[1])
     
     assert len(result_arg_1) == len(result_arg_2)
     
     
     if(symbol == 'eq'):
          for i in range(len(result_arg_1)):
               # if((result_arg_2[i]=='-1') or (result_arg_1[i]=='-1')):
               #      result[i] = '-1'
               #      continue
               if(result_arg_1[i]==result_arg_2[i]):
                    result[i] = '1' 
               else:
                    result[i] = '0'
     
     elif(symbol == 'uneq'):
          for i in range(len(result_arg_1)):
               # if((result_arg_2[i]=='-1') or (result_arg_1[i]=='-1')):
               #      result[i] = '-1'
               #      continue
               if(result_arg_1[i]!=result_arg_2[i]):
                    result[i] = '1' 
               else:
                    result[i] = '0'

     elif(symbol == 'bvand'):
          for i in range(len(result_arg_2)):
               # if((result_arg_2[i]=='-1') or (result_arg_1[i]=='-1')):
               #      result[i] = '-1'
               #      continue
               result[i] =  bitwise_and(result_arg_1[i], result_arg_2[i], bit_width=None)

     elif(symbol == 'bvor'):
          for i in range(len(result_arg_2)):
               # if((result_arg_2[i]=='-1') or (result_arg_1[i]=='-1')):
               #      result[i] = '-1'
               #      continue
               result[i] =  bitwise_or(result_arg_1[i], result_arg_2[i], bit_width=None)

     elif(symbol == 'bvsub'):
          for i in range(len(result_arg_2)):
               # if((result_arg_2[i]=='-1') or (result_arg_1[i]=='-1')):
               #      result[i] = '-1'
               #      continue
               result[i] = bitwise_subtraction(result_arg_1[i], result_arg_2[i], bit_width=None)
     
     elif(symbol == 'bvadd'):
          for i in range(len(result_arg_2)):
               # if((result_arg_2[i]=='-1') or (result_arg_1[i]=='-1')):
               #      result[i] = '-1'
               #      continue
               result[i] = bitwise_addition(result_arg_1[i], result_arg_2[i], bit_width=None)

     elif(symbol == 'bvxor'):
          for i in range(len(result_arg_2)):
               # if((result_arg_2[i]=='-1') or (result_arg_1[i]=='-1')):
               #      result[i] = '-1'
               #      continue
               result[i] = bitwise_xor(result_arg_1[i], result_arg_2[i], bit_width=None)

     
     return result

def reconstruct_concrete_generate_tree(generated_tree, data,pg):
     symbol = generated_tree.app
     if(is_terminal(pg,symbol) and ('const' in symbol)):
          arg = data[symbol][0]
          return SyExp(arg,[])     
     elif(len(generated_tree.args)==2):
          arg_left = reconstruct_concrete_generate_tree(generated_tree.args[0], data,pg)
          arg_right = reconstruct_concrete_generate_tree(generated_tree.args[1], data,pg)
          return SyExp(symbol,[arg_left,arg_right])
     else:
          assert len(generated_tree.args)==0
          return SyExp(symbol,[])


def concat_previous_aassertion(cex_copy,pg,generated_tree,data,inner_cover):
     global mining_collection
     new_generated_tree = reconstruct_concrete_generate_tree(generated_tree, data, pg)
     if(len(mining_collection)==0):
          mining_collection[new_generated_tree] = inner_cover
          print("This is the first assertion")
     elif(len(mining_collection)==3):
          mining_collection[new_generated_tree] = inner_cover
          new_tree = None
          count = 0
          for tree in mining_collection.keys():
               if(count==0):
                    new_tree = tree
               else:
                    new_tree = SyExp("bvand",[new_tree,tree])
               count = count + 1
          cex = None
          count = 0
          for key, value in cex_copy.items():
               if(key not in data):
                    continue
               elif("const" in key):
                    continue
               var = SyExp(key,[])
               val = SyExp(value,[])
               single = SyExp("uneq",[var,val])
               if(count==0):
                    cex = single
               else:
                    cex = SyExp("bvor",[cex,single])
               count = count + 1 
          final_tree =  SyExp("bvand",[cex,new_tree])    
          var_left, var_right = get_all_var(final_tree,pg)
          var_all = var_left + var_right
          smtlib2 = final_tree.to_smt_lib2(var_all, data,"")
          write_to_smt(smtlib2)          
          result = run_pono()
          result_fault = inner_fault_coverage_for_concrete_tree(cex_copy,pg,final_tree)
          assert "unknown" in result
          assert result_fault[0]=='0'
          print("Move to next iteration.")
          path_result = os.path.join(cmd_args.data_root,"result.txt")
          with open(path_result, 'w') as f:
               f.write("find_assumption")
          smtlib2_assump = final_tree.to_smt_lib2(var_all, data, "RTL.")
          write_assumption(smtlib2_assump)
          sys.exit()
     else:
          try:
               if new_generated_tree in mining_collection:
                    # for comb in mining_collection[new_generated_tree]:
                    #      if(comb[0]==data):
                              print("We mined the assertion previously.\n")
                              BreakAllLoops
               # for size in range(1, len(mining_collection) + 1):
               #      for combo in itertools.combinations(mining_collection, size):
               count = 0
               new_tree = None
               for old_tree in mining_collection.keys(): 
                    if(count==0):
                         new_tree = SyExp("bvand",[new_generated_tree,old_tree])
                    else:
                         new_tree = SyExp("bvand",[new_tree,old_tree])
                    count = count + 1
               result = inner_fault_coverage_for_concrete_tree(cex_copy,pg,new_tree)
               if(result[0]=='0'):
                    print("The combination of the previous assertion can block the counterexample, the assertions are\n")
                    print(new_generated_tree.to_py())
                    # for i in range(len(combo)):
                    #      print(combo[i].to_py())
                    var_left, var_right = get_all_var(new_generated_tree,pg)
                    var_all = var_left + var_right
                    smtlib2 = new_generated_tree.to_smt_lib2(var_all, cex_copy, "RTL.")
                    path_result = os.path.join(cmd_args.data_root,"result.txt")
                    with open(path_result, 'w') as f:
                         f.write("find_assumption")
                    smtlib2_assump = final_tree.to_smt_lib2(var_all, data, "RTL.")
                    write_assumption(smtlib2_assump)
                    if cmd_args.exit_on_find:
                         sys.exit()
               print("All the combination cannot be blocked the counterexample")
               
               mining_collection[new_generated_tree] = inner_cover
          except BreakAllLoops:
               pass

def recursive_find_const(dic_value, pg, generate_tree):
     symbol = generate_tree.app
     const_width_pair = {}
     const_width_pair_left = {}
     const_width_pair_right = {}
     initial_width = 0 
     if(is_terminal(pg,symbol)):
          if("const" in symbol):
               const_width_pair[symbol] = initial_width
          else:
               initial_width = len(dic_value[symbol][0])
          return const_width_pair , initial_width
     
     if(len(generate_tree.args) == 2):
          const_width_pair_left, width_left = recursive_find_const(dic_value, pg,generate_tree.args[0])
          const_width_pair_right, width_right = recursive_find_const(dic_value, pg,generate_tree.args[1])
     
     if(len(const_width_pair_left)>0):
          temp = const_width_pair_left.copy()
          for key, value in temp.items():
               assert 'const' in key
               if(value == 0):
                    const_width_pair_left[key] = width_right
     
     
     if(len(const_width_pair_right)>0):
          temp = const_width_pair_right.copy()
          for key, value in temp.items():
               assert 'const' in key
               if(value == 0):
                    const_width_pair_right[key] = width_left
     
     if(symbol == 'eq' or symbol == 'uneq' or symbol == 'bvule' or symbol == 'bvuge'):
          return {**const_width_pair_left, **const_width_pair_right},1
     else:
          if (width_left == 0) or (width_right == 0):
               return {**const_width_pair_left, **const_width_pair_right},width_left + width_right
          else:
               assert width_left == width_right
               return {**const_width_pair_left, **const_width_pair_right},width_left

          
def find_max_coverage_subset(dict_of_lists):
    # 创建一个包含所有1的集合
    all_ones = set(i for lst in dict_of_lists.values() for i, val in enumerate(lst) if val == 1)
    
    # 初始化一个空集合来存储最大覆盖的列表
    max_coverage_subset = set()
    
    while all_ones:
        # 找到覆盖最多1的列表
        best_list = max(dict_of_lists.keys(), key=lambda key: sum(1 for i, val in enumerate(dict_of_lists[key]) if val == 1))
        
        # 添加这个列表到最大覆盖集合中
        max_coverage_subset.add(best_list)
        
        # 更新all_ones，去掉已经被覆盖的1
        all_ones -= {i for i, val in enumerate(dict_of_lists[best_list]) if val == 1}
        
        # 从字典中删除已经覆盖的列表
        del dict_of_lists[best_list]
    
    return max_coverage_subset     

def check_imply_and_save(generated_tree,data_temperal,var_list,pg):
     global mining_collection
     concrete_tree = reconstruct_concrete_generate_tree(generated_tree, data_temperal,pg)
     Flag = False
     keys_to_delete = []
     print("Now check whether the mining assertion can cover previous assertion.")
     if(len(mining_collection)==0):
          mining_collection[generated_tree.to_py(data_temperal)]=[concrete_tree,var_list]
     else:  
          for formula_str, forula_info in mining_collection.items():
               assert len(forula_info)==2          
               new_tree = SyExp("imply",[concrete_tree,forula_info[0]])
               var_all = var_list+ forula_info[1]
               smtlib2 = new_tree.to_smt_lib2(var_all, data_temperal,"")
               result_boolector = check_boolector(smtlib2, var_all, data_temperal)   
               if("unsat" in result_boolector):
                    keys_to_delete.append(formula_str)
               else:
                    assert result_boolector=="sat\n"               
                    new_tree = SyExp("imply",[forula_info[0], concrete_tree])
                    smtlib2 = new_tree.to_smt_lib2(var_all, data_temperal,"")
                    result_boolector = check_boolector(smtlib2, var_all, data_temperal) 
                    if("unsat" in result_boolector):
                         Flag = True
                         break
     if(Flag==False):
          mining_collection[generated_tree.to_py(data_temperal)]=[concrete_tree,var_list]   
          if(len(keys_to_delete)!=0):
             for key in keys_to_delete:
                    del mining_collection[key] 
     else:
          assert len(keys_to_delete)==0                  


def reward_cal(iteration, data_smt, filename, pg , generated_tree, const):

     # x = SyExp("x[14:0]",[])
     # y = SyExp("y[14:0]",[])
     # x_y = SyExp("bvadd",[x,y])
     # const = SyExp("const_0",[])
     # generated_tree = SyExp("bvule",[x_y,const])
     reward_same = decduction_same_symbol(generated_tree,pg)
     width, is_mismatch = width_match(pg,generated_tree,data_smt.formula_dict[filename.replace('.sl', '')])
     reward_deduction = 0
     if(is_mismatch==False):
          if filename.replace('.sl', '') in data_smt.cand_masking:
               reward_deduction,width_mask = deduction_const_connection(generated_tree,pg,data_smt.formula_dict[filename.replace('.sl', '')],data_smt.cand_masking[filename.replace('.sl', '')])
          else:
               reward_deduction,width_mask = deduction_const_connection(generated_tree,pg,data_smt.formula_dict[filename.replace('.sl', '')],{})
     else:
          reward_deduction = -1     
     var_all = get_all_var(generated_tree,pg)

     if(reward_deduction == -1):
          if(cmd_args.remove_deduction_engine):
               return 0,0
          else:
               return reward_same, -1

     index = filename.replace('.sl', '')
     reward_total = 0
     if index in data_smt.cand_masking:
          results = recursive_calculation(data_smt.formula_dict[index] , pg, generated_tree,data_smt.cand_const_add[index], data_smt.cand_const_sub[index],data_smt.cand_masking[index])
     else:
          results = recursive_calculation(data_smt.formula_dict[index] , pg, generated_tree,data_smt.cand_const_add[index], data_smt.cand_const_sub[index],{})
     global mining_collection
     for res in results:
          reward_single = 0
          for key, value in res["result"].items():
               if(int(value)==1):
                    reward_single = reward_single + 1
               
          reward_single = reward_single/len(res["result"].items())
          
          data_temperal = data_smt.formula_dict[index].copy()
          if(reward_single>0.999999):
                    ## Now we should start the fault coverage analysis
               for key, value in res.items():
                    if(key == "result"):
                         continue
                    else:
                         data_temperal[key] = value
               smtlib2 = generated_tree.to_smt_lib2(var_all, data_temperal,"")
               result_boolector = check_boolector(smtlib2, var_all, data_temperal)    
               if("unsat" not in result_boolector):
                    if(cmd_args.cal_pass_at_k):
                         cal_pass_at_k(iteration,filename)   
               if((generated_tree.to_py(data_temperal) not in mining_collection) or cmd_args.run_ablition):
                
                    if("unsat" in result_boolector):
                         if(cmd_args.remove_deduction_engine==False):
                              reward_single = - 1
                         # continue
                    else:
                         assert result_boolector=="sat\n"
                         if cmd_args.use_smt_switch:
                              print("Found a solution: " + generated_tree.to_py(data_temperal))
                              # print("The inner coverage is %.2f" %((1 - miss_fault / len(data_smt.fault_pattern[index]))))
                              write_to_file(index,generated_tree,None, data_temperal)
                         else:
                           
                              print("Found a potential solution: " + generated_tree.to_py(data_temperal))
                              write_to_smt(smtlib2)
                              random_key = random.choice(list(data_temperal.keys()))
                              result,assertion_path = run_pono(len(data_temperal[random_key]))
                              if("unknown" in result):
                                   print("Found a solution: " + generated_tree.to_py(data_temperal))
                                   # print("The inner coverage is %.4f" %((1 - miss_fault / len(data_smt.fault_pattern[index]))))

                                   write_to_file(index,generated_tree, None, data_temperal)
                                   check_imply_and_save(generated_tree,data_temperal,var_all,pg)
                                   
                                   shutil.rmtree(os.path.join(cmd_args.data_root,'assertion'))
                                   if(os.path.exists(os.path.join(cmd_args.data_root,'verilog_assertion'))):
                                        shutil.rmtree(os.path.join(cmd_args.data_root,'verilog_assertion'))
                                   for formula,formula_info in mining_collection.items():
                                        smtlib2 = formula_info[0].to_smt_lib2(formula_info[1], data_temperal,"")
                                        write_to_smt(smtlib2)
                                        write_to_verilog(formula_info[0])
                                   if(len(mining_collection)==5):
                                        sys.exit()
               reward_total += reward_single                           
          else:
               reward_total = reward_single + reward_total
     
     return (reward_total / len(results)) + reward_same, 0


     
     if const != 0:
          # We need to find a more suitable method to calculate the const width and the number of const
          static_analysis_add_sub(data_smt.formula_dict[index])    
          const_width, width_0 = recursive_find_const(data_smt.formula_dict[index],pg ,generated_tree)
          assert width_0 == 1
          permutations = {}
          for var, width in const_width.items():    
               binary_numbers = [''.join(seq) for seq in itertools.product('01', repeat=width)]
               permutation = list(itertools.product(binary_numbers, repeat=1))
               permutations[var] = permutation
          
          all_keys = list(permutations.keys())
          all_values = [permutations[key] for key in all_keys]
          all_combinations = []

          for combination_values in itertools.product(*all_values):
               combination = {key: value for key, value in zip(all_keys, combination_values)}
               all_combinations.append(combination)
          
          ## We need to calculate the waveform length, we only need to capture one of the variable 
          values = data_smt.formula_dict[index].values()
          length = 0
          for value in values:
               length = len(value)
               break
          ## We can calculate the average rewards 
          reward_total = 0 
          for i, permutation in enumerate(all_combinations, start=1):
               reward_single = 0
               data_temperal = data_smt.formula_dict[index].copy()
               for var,val in permutation.items():
                    dict_value = []
                    for j in range(length):
                         dict_value.append(val[0])
                    data_temperal[var] = dict_value
               
               result = recursive_calculation(data_temperal, pg, generated_tree)
               # if '-1' in result:
               #      return -2
               # else:
               for key, value in result.items():
                    if(int(value)==1):
                         reward_single = reward_single + 1
               
               reward_single = reward_single/len(result.items())
                    
               if(reward_single>0.999999):
                    ## Now we should start the fault coverage analysis
                    miss_fault = 0
                    
                    for pattern in data_smt.fault_pattern[index]:
                         fault_temperal = pattern.copy()
                         # assert len(permutation)==1
                         for var,value in permutation.items():
                              fault_temperal[var] = value[0]                   
                         result = inner_fault_coverage(fault_temperal, pg, generated_tree)
                         if(result[0]=='1'):
                              miss_fault += 1
                    if(miss_fault / len(data_smt.fault_pattern[index])==1):
                         reward_single = 0
                    else:
                         reward_single = reward_single + (1 - miss_fault / len(data_smt.fault_pattern[index]))
                         if cmd_args.use_smt_switch:
                              print("Found a solution: " + generated_tree.to_py(data_temperal))
                              print("The inner coverage is %.2f" %((1 - miss_fault / len(data_smt.fault_pattern[index]))))
                              write_to_file(index,generated_tree,(1 - miss_fault / len(data_smt.fault_pattern[index])), data_temperal)
                         else:
                              smtlib2 = generated_tree.to_smt_lib2(var_all, data_temperal,"")
                              print("Found a potential solution: " + generated_tree.to_py(data_temperal))
                              write_to_smt(smtlib2)
                              result = run_pono()
                              if("unknown" in result):
                                   print("Found a solution: " + generated_tree.to_py(data_temperal))
                                   print("The inner coverage is %.4f" %((1 - miss_fault / len(data_smt.fault_pattern[index]))))
                                   write_to_file(index,generated_tree, (1 - miss_fault / len(data_smt.fault_pattern[index])), data_temperal)
                                   
                                   if cmd_args.exit_on_find:
                                        ##Now we need to check whether this assignment can block the counterexample
                                        cex_copy = data_smt.cex.copy()
                                        for var,value in permutation.items():
                                             cex_copy[var] = value[0]
                                        print("Start to check whether the assertion can block the cex")
                                        result = inner_fault_coverage(cex_copy, pg, generated_tree)
                                        if(result[0]=='1'):
                                             print("The counterexample cannot be blocked, now let\'s try to connect with previous assertion")
                                             concat_previous_aassertion(cex_copy,pg,generated_tree, data_temperal,1-miss_fault / len(data_smt.fault_pattern[index]))
                                        else:
                                             smtlib2 = generated_tree.to_smt_lib2(var_all, data_temperal, "RTL.")
                                             path_result = os.path.join(cmd_args.data_root,"result.txt")
                                             with open(path_result, 'w') as f:
                                                  f.write("find_assumption")
                                             write_assumption(smtlib2)
                                             sys.exit()
                              else:
                                   print("The potential solution is not passed by BMC ")

               reward_total += reward_single 
               reward = reward_total/len(all_combinations)

     
     elif(const==0):
          reward = 0
          static_analysis_add_sub(data_smt.formula_dict[index])
          result = recursive_calculation(data_smt.formula_dict[index], pg, generated_tree)
          # if '-1' in result:
          #      return -2
          # else:
          for key, value in result.items():
               if(int(value)==1):
                    reward = reward + 1   
          reward = reward/len(result.items())
          if(reward>0.999999):
               miss_fault = 0
               
               for pattern in data_smt.fault_pattern[index]:
                    fault_temperal = pattern.copy()                
                    result = inner_fault_coverage(fault_temperal, pg, generated_tree)
                    if(result[0]=='1'):
                         miss_fault += 1
               
               if(miss_fault / len(data_smt.fault_pattern[index])==1):
                    reward = 0
               else:
                    # reward = reward + (1 - miss_fault / len(data_smt.fault_pattern))
                    if cmd_args.use_smt_switch:
                         reward = (1 - miss_fault / len(data_smt.fault_pattern[index])) +reward
                         print("Found a solution: " + generated_tree.to_py())
                         print("The inner coverage is %.2f" %((1 - miss_fault / len(data_smt.fault_pattern[index]))))
                         write_to_file(index,generated_tree,(1 - miss_fault / len(data_smt.fault_pattern[index])))
                    else:
                         smtlib2 = generated_tree.to_smt_lib2(var_all, data_smt.formula_dict[index])
                         print("Found a potential solution: " + generated_tree.to_py())
                         write_to_smt(smtlib2)
                         result = run_pono()
                         if("unknown" in result):
                              print("Found a solution: " + generated_tree.to_py())
                              # print("The inner coverage is %.2f" %((1 - miss_fault / len(data_smt.fault_pattern))))
                              write_to_file(index,generated_tree,(1 - miss_fault / len(data_smt.fault_pattern[index])))
                              if cmd_args.exit_on_find:
                                   cex_copy = data_smt.cex.copy()
                                   for var,value in permutation.items():
                                        cex_copy[var] = value[0]
                                   print("Start to check whether the assertion can block the cex")
                                   result = inner_fault_coverage(cex_copy, pg, generated_tree)
                                   if(result[0]=='1'):
                                        print("The counterexample cannot be blocked, now let\'s try to connect with previous assertion")
                                        concat_previous_aassertion(cex_copy,pg,generated_tree, {},miss_fault / len(data_smt.fault_pattern[index]))
                                   else:
                                        smtlib2 = generated_tree.to_smt_lib2(var_all ,"RTL.")
                                        path_result = os.path.join(cmd_args.data_root,"result.txt")
                                        with open(path_result, 'w') as f:
                                             f.write("find_assumption")
                                        write_assumption(smtlib2)
                                        sys.exit()
                         else:
                              print("The potential solution is not passed by BMC ")
               

def cal_pass_at_k(iteration,filename):
     assert cmd_args.pass_at_k_file!=None
     with open(cmd_args.pass_at_k_file, 'a+') as f:
          f.write("pass at iteration: " + str(iteration) + "\n")



# def reward_const_random(iteration, data_smt, filename, pg , generated_tree):

#      # x = SyExp("x[10:0]",[])
#      # y = SyExp("const0",[])
#      # x_y = SyExp("eq",[x,y])
#      # const = SyExp("const_1",[])
#      # generated_tree = SyExp("eq",[x_y,const])
#      reward_same = decduction_same_symbol(generated_tree,pg)
#      width, is_mismatch = width_match(pg,generated_tree,data_smt.formula_dict[filename.replace('.sl', '')])
#      reward_deduction = 0
#      if(is_mismatch==False):
#           if filename.replace('.sl', '') in data_smt.cand_masking:
#                reward_deduction,width_mask = deduction_const_connection(generated_tree,pg,data_smt.formula_dict[filename.replace('.sl', '')],data_smt.cand_masking[filename.replace('.sl', '')])
#           else:
#                reward_deduction,width_mask = deduction_const_connection(generated_tree,pg,data_smt.formula_dict[filename.replace('.sl', '')],{})
#      else:
#           reward_deduction = -1     
#      var_left, var_right = get_all_var(generated_tree,pg)
#      var_all = var_left + var_right
#      index = filename.replace('.sl', '')
#      if(reward_deduction == -1):
#           if(cmd_args.remove_deduction_engine):
#                return 0,0
#           else:
#                return reward_same, -1
#      else:
#           results = recursive_calculation_random(data_smt.formula_dict[index] , pg, generated_tree,{}, {},{})
#           global mining_collection
#           reward_total = 0
#           for res in results:
#                reward_single = 0
#                for key, value in res["result"].items():
#                     if(int(value)==1):
#                          reward_single = reward_single + 1
#                reward_single = reward_single/len(res["result"].items())
               
#                data_temperal = data_smt.formula_dict[index].copy()
#                if(reward_single>0.999999):
#                          ## Now we should start the fault coverage analysis
#                     for key, value in res.items():
#                          if(key == "result"):
#                               continue
#                          else:
#                               data_temperal[key] = value
#                     smtlib2 = generated_tree.to_smt_lib2(var_all, data_temperal,"")
#                     result_boolector = check_boolector(smtlib2, var_all, data_temperal)    
#                     if("unsat" not in result_boolector):
#                          assert result_boolector=="sat\n"
#                          if(cmd_args.cal_pass_at_k):
#                               cal_pass_at_k(iteration,filename)   
#                     if((generated_tree.to_py(data_temperal) not in mining_collection) or cmd_args.run_ablition):                  
#                          if("unsat" in result_boolector):
#                               if(cmd_args.remove_deduction_engine):
#                                    reward_single = - 1 
#                          else:
#                               assert result_boolector=="sat\n"
#                               if cmd_args.use_smt_switch:
#                                    print("Found a solution: " + generated_tree.to_py(data_temperal))
#                                    write_to_file(index,generated_tree,None, data_temperal)
#                               else:
                              
#                                    print("Found a potential solution: " + generated_tree.to_py(data_temperal))
#                                    write_to_smt(smtlib2)
#                                    random_key = random.choice(list(data_temperal.keys()))
#                                    result,assertion_path = run_pono(len(data_temperal[random_key]))
#                                    if("unknown" in result):
#                                         print("Found a solution: " + generated_tree.to_py(data_temperal))
#                                         # print("The inner coverage is %.4f" %((1 - miss_fault / len(data_smt.fault_pattern[index]))))

#                                         write_to_file(index,generated_tree, None, data_temperal)
#                                         check_imply_and_save(generated_tree,data_temperal,var_all,pg)
#                                         shutil.rmtree(os.path.join(cmd_args.data_root,'assertion'))
#                                         if(os.path.exists(os.path.join(cmd_args.data_root,'verilog_assertion'))):
#                                              shutil.rmtree(os.path.join(cmd_args.data_root,'verilog_assertion'))
#                                         for formula,formula_info in mining_collection.items():
#                                              smtlib2 = formula_info[0].to_smt_lib2(formula_info[1], data_temperal,"")
#                                              write_to_smt(smtlib2)
#                                              write_to_verilog(formula_info[0])
#                                         if(len(mining_collection)==5):
#                                              sys.exit()
#                     reward_total += reward_single                           
#                else:
#                     reward_total = reward_single + reward_total
#           if(cmd_args.remove_deduction_engine and cmd_args.use_random_action):
#                return (reward_total / len(results)) + reward_same, 0
#           else:
#                return 0,0
     

def write_to_file(filename,generated_tree,fault_coverage,var_value={}):
     
     if cmd_args.use_smt_switch:
          path = os.path.join(cmd_args.data_root,filename+".txt")
     else:
          path = os.path.join(cmd_args.data_root,"mining_result")
     # if(os.path.exists(path)==False):
     #      with open(path, 'w') as f:
     #           f.write("\nFound a solution: " + generated_tree.to_py(var_value))
     with open(path, 'a+') as f:
          f.write("\nFound a solution:%s" %(generated_tree.to_py(var_value)))

def write_to_smt(smt2):
     path_folder = os.path.join(cmd_args.data_root,'assertion')
     # path = os.path.join(path_folder,str(cmd_args.iteration))
     if(os.path.exists(path_folder)==False):
          os.makedirs(path_folder)
          assertion_path = os.path.join(path_folder,'assertion' + '0' + '.smt2')
          with open(assertion_path, 'w') as f:
               f.write(smt2)
     else:
          file_count = len([f for f in os.listdir(path_folder) if os.path.isfile(os.path.join(path_folder, f))])
          assertion_path = os.path.join(path_folder,'assertion' + str(file_count)+ '.smt2')
          with open(assertion_path, 'w') as f:
               f.write(smt2)


def write_to_verilog(generated_tree,var_value = {}):

     verilog_path_folder = os.path.join(cmd_args.data_root,'verilog_assertion')
     if(os.path.exists(verilog_path_folder)==False):
          os.makedirs(verilog_path_folder)
          assertion_path = os.path.join(verilog_path_folder,'verilog' + '0' + '.txt')
          with open(assertion_path, 'w') as f:
               f.write(generated_tree.to_verilog())
     else:
          file_count = len([f for f in os.listdir(verilog_path_folder) if os.path.isfile(os.path.join(verilog_path_folder, f))])
          assertion_path = os.path.join(verilog_path_folder,'verilog' + str(file_count)+ '.txt')
          with open(assertion_path, 'w') as f:
               f.write(generated_tree.to_verilog())
               
def write_assumption(smt2):
     path = os.path.join(cmd_args.data_root,'envinv.smt2')
     if(os.path.exists(path)):
          with open(path, 'r') as file:
               line_count = len(file.readlines())
          smt_assumption = smt2.replace("assertion.0", "assumption."+str(line_count))
     else:

          smt_assumption = smt2.replace("assertion.0", "assumption.0")

     with open(path, 'a+') as f:
               f.write(smt_assumption + '\n')


def main():  
     a = '1011'
     b = '0101'
     
     result = bitwise_addition(a, b)
     c = '0011'
     d = '0101'
     result_1 = bitwise_subtraction(c, d)
     result_xor = bitwise_xor(c, d)
     print(result,result_1,result_xor)