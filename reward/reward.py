import tqdm
import sys
from common.cmd_args import cmd_args
from reward.deduction import *
import os
import random 
import itertools
from reward.third_party import run_pono
from parser_syg.sygus_parser import *

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

def recursive_calculation(dic_value, pg, generate_tree):

     symbol = generate_tree.app
     result = {}
     if(is_terminal(pg,symbol)):
          for i in range(len(dic_value[symbol])):
               result[i] = dic_value[symbol][i]
          return result

     if(len(generate_tree.args)==2):
          result_arg_1 = recursive_calculation( dic_value, pg, generate_tree.args[0])
          result_arg_2 = recursive_calculation( dic_value, pg, generate_tree.args[1])
     
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
     
     elif(symbol == 'uneq'):
          for i in range(len(result_arg_1)):
               if((result_arg_2[i]=='-1') or (result_arg_1[i]=='-1')):
                    result[i] = '-1'
                    continue
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
     
     if(symbol == 'eq' or symbol == 'uneq'):
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

def reward_cal(data_smt, filename, pg , generated_tree, const,previous_reward_same):
     width, is_mismatch = width_match(pg,generated_tree,data_smt.formula_dict[filename.replace('.sl', '')])
     reward_same = decduction_same_symbol(generated_tree,pg)
     reward_same = reward_same - previous_reward_same
     var_left, var_right = get_all_var(generated_tree,pg)
     var_all = var_left + var_right
     all_contains_const = all("const" in item for item in var_all)
     if(is_mismatch ==True and all_contains_const==True):
          return 0, -2
     elif(is_mismatch ==True or all_contains_const==True):
          return 0, -1
     index = filename.replace('.sl', '')
     
     if const != 0:
          # We need to find a more suitable method to calculate the const width and the number of const
              
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
                         reward_single = reward_single + (1 - miss_fault / len(data_smt.fault_pattern))
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
                                   print("The inner coverage is %.2f" %((1 - miss_fault / len(data_smt.fault_pattern[index]))))
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
               

     
     return reward + reward_same, 0

def write_to_file(filename,generated_tree,fault_coverage,var_value={}):
     path = os.path.join(cmd_args.data_root,filename +"mining_result")
     # if(os.path.exists(path)==False):
     #      with open(path, 'w') as f:
     #           f.write("\nFound a solution: " + generated_tree.to_py(var_value))
     with open(path, 'a+') as f:
          f.write("\nFound a solution:%s, the coverage is %.2f" %(generated_tree.to_py(var_value),fault_coverage))

def write_to_smt(smt2):
     path_folder = os.path.join(cmd_args.data_root,'assertion')
     path = os.path.join(path_folder,str(cmd_args.iteration))
     if(os.path.exists(path)==False):
          os.makedirs(path)
          assertion_path = os.path.join(path,'assertion' + '0' + '.smt2')
          with open(assertion_path, 'w') as f:
               f.write(smt2)
     else:
          file_count = len([f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))])
          assertion_path = os.path.join(path,'assertion' + str(file_count)+ '.smt2')
          with open(assertion_path, 'w') as f:
               f.write(smt2)

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