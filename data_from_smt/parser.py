import os
import torch
from parser_syg.sygus_parser import SyExp,match_p,separate_p
import random
import itertools
from reward.reward import bitwise_subtraction, bitwise_addition, static_analysis_eq
from common.cmd_args import *

class data_from_smt(object):
     def __init__(self):
          self.formula_dict = {}
          self.formula_dict_label = {}
          self.formula_dict_tensor = {}
          self.formula_count = {}
          self.combinations_dict = {}
          self.cand_masking = {}
          self.fault_pattern = {}
          # self.using_COI = using_COI
          self.cex = {}
          self.cand_const_add = {}
          self.cand_const_sub = {}
          
     def static_analysis_add_sub(self,dic_value,current_formula):
          bit_widths = {key: len(dic_value[key][0]) for key in dic_value}

          bit_width_groups = {}
          for key, bit_width in bit_widths.items():
               if bit_width not in bit_width_groups:
                    bit_width_groups[bit_width] = [key]
               else:
                    bit_width_groups[bit_width].append(key)
          
          candidate_key_combinations = []
          for width, group in bit_width_groups.items():
               # if len(group) >= 3:
               #      for r in range(2, 4):
               #           for combo in itertools.combinations(group, r):
               #                candidate_key_combinations.append(combo)
               if len(group) >= 2:
                    for r in range(2, 3):
                         for combo in itertools.combinations(group, r):
                              candidate_key_combinations.append(combo)          
               else:
                    assert len(group) == 1
                    assert width not in self.cand_const_add

                    if(current_formula not in self.cand_const_add):
                         dict_eq = {}
                         dict_eq[width] = static_analysis_eq(dic_value[group[0]])
                         self.cand_const_add[current_formula] =dict_eq
                         self.cand_const_sub[current_formula] =dict_eq
                    else:
                         self.cand_const_add[current_formula][width] = static_analysis_eq(dic_value[group[0]])
                         self.cand_const_sub[current_formula][width] = static_analysis_eq(dic_value[group[0]])
          
          dict_add = {}     
          dict_sub = {}     
          if(len(candidate_key_combinations)!=0):

               for key_combination in candidate_key_combinations:
                    result_add = []
                    result_sub = []
                    for i in range(len(dic_value[key_combination[0]])):
                         result_add.append(bitwise_addition(dic_value[key_combination[0]][i],dic_value[key_combination[1]][i]))
                         result_sub.append(bitwise_subtraction(dic_value[key_combination[0]][i],dic_value[key_combination[1]][i]))
                         result_sub.append(bitwise_subtraction(dic_value[key_combination[1]][i],dic_value[key_combination[0]][i]))
                    for i in range(len(result_add)):
                         if result_add[i] in dict_add:
                              dict_add[result_add[i]] = dict_add[result_add[i]] + 1 
                         else:
                              dict_add[result_add[i]] = 1
                    for i in range(len(result_sub)):
                         if result_sub[i] in dict_sub:
                              dict_sub[result_sub[i]] = dict_sub[result_sub[i]] + 1 
                         else:
                              dict_sub[result_sub[i]] = 1

               cand_const_add_single = {}
               cand_const_sub_single = {}
               for val in dict_add.keys():
                    width_value = len(val)
                    
                    if(width_value in cand_const_add_single):
                         cand_const_add_single[width_value][val]= dict_add[val]
                    else:
                         temp= {}
                         temp[val] = dict_add[val]
                         cand_const_add_single[width_value] = temp
               for val in dict_sub.keys():
                    width_value = len(val)
                    if(width_value in cand_const_sub_single):
                         cand_const_sub_single[width_value][val]= dict_sub[val]
                    else:
                         temp= {}
                         temp[val] = dict_sub[val]
                         cand_const_sub_single[width_value] = temp
               
               cand_const_add_single_reduce = {}
               for width, value_dict in cand_const_add_single.items():
                    if(len(cand_const_add_single[width])==1):
                         cand_const_add_single_reduce[width] = list(cand_const_add_single[width].keys())
                    else:
                         sorted_count_dict_add = dict(sorted(value_dict.items(), key=lambda item: item[1], reverse=True)[:2])   
                    
                         value_list = list(value_dict.keys())
                         decimal_numbers = [int(binary, 2) for binary in value_list]
                         max_decimal, max_binary = max(zip(decimal_numbers, value_list))
                         min_decimal, min_binary = min(zip(decimal_numbers, value_list))
                         sorted_count_dict_add[max_binary] = 0
                         sorted_count_dict_add[min_binary] = 0
                         cand_const_add_single_reduce[width] = list(sorted_count_dict_add.keys())
               
               cand_const_sub_single_reduce = {}
               for width, value_dict in cand_const_sub_single.items():
                    if(len(cand_const_add_single[width])==1):
                         cand_const_sub_single_reduce[width] = list(cand_const_add_single[width].keys())
                    else:
                         sorted_count_dict_sub = dict(sorted(value_dict.items(), key=lambda item: item[1], reverse=True)[:2]) 
                         
                         value_list = list(value_dict.keys())
                         decimal_numbers = [int(binary, 2) for binary in value_list]
                         max_decimal, max_binary = max(zip(decimal_numbers, value_list))
                         min_decimal, min_binary = min(zip(decimal_numbers, value_list))
                         sorted_count_dict_sub[max_binary] = 0
                         sorted_count_dict_sub[min_binary] = 0               
                         cand_const_sub_single_reduce[width] = list(sorted_count_dict_sub.keys())                   
               if(current_formula in self.cand_const_add):
                    for key,value in cand_const_add_single_reduce.items():
                         assert key not in self.cand_const_add[current_formula]
                         self.cand_const_add[current_formula] = value
               else:
                    self.cand_const_add[current_formula] = cand_const_add_single_reduce
               if(current_formula in self.cand_const_sub):
                         assert key not in self.cand_const_sub[current_formula]
                         self.cand_const_sub[current_formula] = value               
               else:
                    self.cand_const_sub[current_formula] = cand_const_sub_single_reduce
     
     def load_to_combinations_dict(self,current_formula):
          ### we can randomly select the first key, because the length is the same
          first_key = list(self.formula_dict[current_formula].keys())[0]
          length = len(self.formula_dict[current_formula][first_key])
          key_value_in_cycle = {}
          for i in range(length):
               single_cycle = {}
               for key, value in self.formula_dict[current_formula].items():
                    assert len(value) == length
                    single_cycle[key]  = self.formula_dict[current_formula][key][i]
               key_value_in_cycle[i] = single_cycle
          self.combinations_dict[current_formula] = key_value_in_cycle
          
     def load_smt_switch(self,fname):
          with open(fname, 'r') as file:
               lines = file.readlines()

          current_formula = None
          
          for line in lines:
               line = line.strip()
               if line.startswith("Formula:"):
                    if(current_formula is not None):
                         self.formula_dict[current_formula] = current_variables.copy()
                         self.formula_dict_label[current_formula] = label.copy()
                         self.static_analysis_add_sub(self.formula_dict[current_formula],current_formula)
                         self.load_to_combinations_dict(current_formula)
                    current_formula = line.split(":", 1)[1].strip()
                    label = self.parse_ground_truth(current_formula)
                    if current_formula in self.formula_dict:
                         self.repeat_count(current_formula)
                         current_formula = current_formula + "_" + str(self.formula_count[current_formula])
                    self.formula_dict[current_formula] = {}
                    current_variables = {}
               elif line.isdigit():
                    continue
               else:
                    variable_name, variable_value = line.split(":", 1)[0], line.split(":", 1)[1]
                    
                    if variable_name in current_variables:
                         current_variables[variable_name].append(variable_value)
                    else:
                         current_variables[variable_name] = [variable_value]
          
          ## There is still has the last formula
          self.formula_dict[current_formula] = current_variables.copy()
          self.formula_dict_label[current_formula] = label.copy()
          self.static_analysis_add_sub(self.formula_dict[current_formula],current_formula)
     
     def parse_ground_truth(self,name):
          name = separate_p(name)
          label_list = []
          vs = name.split()
          if len(vs) == 0:
               return []
          if vs[0] == '(':
               app = vs[1]  # app name follows the left parenthesis

          if vs[0] == '(':
               app = vs[1]  # app name follows the left parenthesis
               if(app=="="):
                    app = 'eq'
               elif (app=="!="):
                    app = "uneq"

               # locate the right parenthesis
               r = match_p(vs, 0)
               assert r > 0

               if app == "(":
                    #app = "_TUPLE_"
                    app = ""
                    label_list = label_list + self.parse_ground_truth( " ".join(vs[1:r]) )
               else:
                    label_list = label_list + self.parse_ground_truth( " ".join(vs[2:r]) )

               label_list.append(app)
               label_list = label_list + self.parse_ground_truth(" ".join(vs[r+1:]) )
               return label_list

          else:
               label_list.append(vs[0])
               label_list = label_list + self.parse_ground_truth(" ".join(vs[1:]))
               return label_list

     def enlarge_waveform(self):
          for key_top,value in self.formula_dict.items():
               list_length = len(next(iter(self.formula_dict[key_top].values())))

               patterns = {i: [self.formula_dict[key_top][key][i] for key in self.formula_dict[key_top]] for i in range(list_length)}

               existing_patterns = list(patterns.values())
               for i in range(1000 - list_length):
                    selected_pattern = random.choice(existing_patterns)
                    
                    count = 0
                    for key in self.formula_dict[key_top]:
                         self.formula_dict[key_top][key].append(selected_pattern[count])
                         count +=1

     def dump_to_template(self,fname):
          if(os.path.exists("./grammar_gen")==False):
               os.makedirs("./grammar_gen")
          
          filename = os.path.basename(fname)
          file_without_extension = os.path.splitext(filename)[0]
          path_for_fname = os.path.join("./grammar_gen",file_without_extension)

          if(os.path.exists(path_for_fname)==False):
               os.makedirs(path_for_fname)
          
          assert os.path.exists("./grammar/template.sl")
          with open("./grammar/template.sl", 'r') as file:
               lines = file.read()
          for formula, data_all in self.formula_dict.items():
               template_file = os.path.join(path_for_fname,formula + ".sl")
               content_skel = []
               content_var = []
               for var in data_all:
                    content_skel.append(" (" + var + " Bool" +")")
                    content_var.append(var)
                    aligned_variables = [content_var[0]] + [f'{" " * 44}{v}' for v in content_var[1:]]
               lines_new = lines.replace('skel ()', f'skel ({"".join(f"{v}" for v in content_skel)}  )')
               lines_new = lines_new.replace('variable', '\n'.join(aligned_variables))
               with open(template_file,'w') as file:
                    file.write(lines_new)
          return path_for_fname    

     def generate_fault_pattern(self,variables, combination, current_variable_index,index):
          if current_variable_index == len(variables):
               count = 0
               flag = 0
               for key, value in self.combinations_dict[index].items():
                    count += 1
                    if value == combination:
                         flag = 1
                         # print(f"查询到组合 {key}: {combination}")
                         break
               if(count == len(self.combinations_dict[index]) and flag == 0):
                    combination_copy = combination.copy()
                    if(index in self.fault_pattern):
                         self.fault_pattern[index] = self.fault_pattern[index] + [combination_copy]
                    else:
                         self.fault_pattern[index] = [combination_copy]
          else:
               variable = list(variables.keys())[current_variable_index]
               num_bits = len(variables[variable][0])
               for value in range(2 ** num_bits):
                    combination[variable] = f"{value:0{num_bits}b}"
                    self.generate_fault_pattern(variables, combination, current_variable_index + 1, index)
                    
     def repeat_count(self,formula):
          assert formula in self.formula_dict
          if formula in self.formula_count:
               self.formula_count[formula] += 1
          else:
               self.formula_count[formula] = 1
     
     def S2Vgraph(self,device):
          for formula, data_all in self.formula_dict.items():
               self.formula_dict_tensor[formula] = {}
               # if(formula =='(= t (bvor (bvand x y) z))_1'):
               #      print(formula)
               for var in data_all:
                    numeric_list = [[[int(string, 2),len(string)]] for string in data_all[var]]
                    self.formula_dict_tensor[formula][var] = torch.tensor(numeric_list, dtype=torch.float).squeeze(1).to(device)


if __name__ == "__main__":
     path = "/data/zhiyuany/property_mining/data/data_collection_symbols.txt"
     data_smt = data_from_smt()
     data_smt.load_smt_switch(path)
     for formula, data_all in data_smt.formula_dict.items():
          print(f"{formula}:")
          for var in data_all:
               print(var,data_all[var])
     data_smt.dump_to_template(path)