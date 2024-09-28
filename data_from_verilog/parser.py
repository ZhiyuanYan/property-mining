import os
import torch
import re
# from parser_syg.sygus_parser import SyExp,match_p,separate_p
import itertools
import shutil
from reward.reward import bitwise_subtraction, bitwise_addition, static_analysis_eq
from common.cmd_args import *
class data_from_verilog(object):
     def __init__(self):
          self.formula_dict = {}
          self.COI_variable = {}
          self.formula_dict_tensor = {}
          self.combinations_dict = {}
          self.fault_pattern = {}
          # self.using_COI = using_COI
          self.cex = {}
          self.cand_const_add = {}
          self.cand_const_sub = {}
          self.cand_masking = {}
          self.pattern_count = {}
          self.formula_dict_without_reduce = {}
     
     def extract_bits(self, number_str, left_index, right_index):
          # number_str = '0101'
          # left_index = 2
          # right_index = 0
          reversed_str = number_str[::-1]
          extracted_value = reversed_str[right_index:left_index + 1][::-1]
          return extracted_value
     
     def load_verilog(self,fname):
          pattern = re.compile(r'^x+$')
          
          
          ## We first parse the COI variables we got from cosa2. In the DreamMiner we do not need to care it.
          # if os.path.exists("COI.txt"):
               
          
          #      with open("COI.txt", 'r') as coi_file:
          #           lines_coi = coi_file.readlines()
               
          #      for line in lines_coi:
          #           line_info = line.strip()
          #           line_split = line_info.split()
                    
          #           if(line_split[0].startswith('RTL.')==False):
          #                continue
                    
          #           var = line_split[0].replace('RTL.','')
          #           for i in range(int(line_split[1])):
          #                left = line_split[(i+1)*2]
          #                right = line_split[(i+1)*2+1]
          #                if i == 0:
          #                     self.COI_variable[var] =[var+'['+left+':'+right+']']
          #                else:
          #                     self.COI_variable[var].append((var+'['+left+':'+right+']'))
          #                assert line_split[-1].startswith('#b')
          #                value = line_split[-1].replace('#b','')
          #                extracted_val = self.extract_bits(value, int(left), int(right))
          #                self.cex[var+'['+left+':'+right+']'] = extracted_val
          
          
          with open(fname, 'r') as file:
               lines = file.readlines()
          # current_formula = None
          if("#b" not in lines[0]):
               lines.pop(0)
          
          variable_width = self.build_formula_dict(lines,True, fname, pattern)
          # variable_width = self.build_formula_dict(lines,False, fname, pattern)
          
          name, ext = os.path.splitext(fname)
          
          self.static_analysis_add_sub(self.formula_dict[os.path.basename(name)],os.path.basename(name))
          self.static_analysis_mask(os.path.basename(name))
          ##Now lets generate a fault pattern
          # self.generate_fault_pattern(variable_width,{},0,os.path.basename(name))

     def insert_to_coi_variable(self,lines):
          line = lines[0]
          line = line.strip()
          parts = line.split(', ')
          for part in parts:
               # 分割变量名和值
               variable, value = part.split(": ")
               # 计算值的长度
               if(value.startswith("#b")):
                    value = value[2:]
               if(value.endswith(",")):
                    value = value[:-1]
               length = len(value)
               # 创建一个包含切片表示的列表
               value_list = [f"{variable}[{length-1}:0]"]
               # 将变量名和对应的列表添加到字典中
               self.COI_variable[variable] = value_list
 
     
     def build_formula_dict(self, lines, is_reduce, fname, pattern):
          seen_lines = set()
          current_variables = {}
          comb_in_one_clcle = {}    
          count = 0      
          for line in lines:
               if(is_reduce):
                    if line not in seen_lines: 
                         seen_lines.add(line)
                    else:
                         continue
               
               # if skip_first_line:
               #      skip_first_line = False
               #      continue
               
               line = line.strip()
               parts = line.split(', ')
               
               for part in parts:
                    # if(parts==""):
                    #      continue
                    split = part.split(': ')
                    variable_name = split[0].strip()
                    if(((variable_name in self.COI_variable.keys())==False) and os.path.exists("COI.txt")):
                         continue
                    else:
                         if(count==0):
                              assert len(self.COI_variable)==0
                              self.insert_to_coi_variable(lines)
                              count = count + 1
                    
                    
                    value = split[1].strip()
                    if(value.startswith("#b")):
                         value = value[2:]
                    if(value.endswith(",")):
                         value = value[:-1]
                    for var in self.COI_variable[variable_name]:
                         match = re.search(r'\[(\d+):(\d+)\]', var)
                         assert match
                         # value ='021213223'
                         start = int(match.group(1))
                         end = int(match.group(2))
                         # Note that this is for the previous prokect, which need to crop the value
                         # First we reverse the value
                         reversed_value = value[::-1]

                         # slice according the start and end
                         cropped_reversed = reversed_value[end:start+1]

                         # reverse back
                         cropped_value = cropped_reversed[::-1]

                         if var in current_variables:
                              current_variables[var].append(cropped_value)
                         else:
                              current_variables[var] = [cropped_value]     
                         # comb_in_one_clcle[var]  = cropped_value  
                    
                    # self.combination[count] = comb_in_one_clcle
          ##We want to remove those only has x value and try to create a dictionary to generate the fault pattern
          
          keys_to_delete = []
          variable_width = {}
          for i in range(len(current_variables[list(current_variables.keys())[0]])):
               self.combinations_dict[i] = {}
          for key, values in current_variables.items():
               if all(pattern.match(val) for val in values):
                    keys_to_delete.append(key)
               else:
                    for i, value in enumerate(values):
                         value_replace = value.replace('x','0')
                         current_variables[key][i] = value_replace
                         comb_in_one_clcle[key] = value_replace
                         self.combinations_dict[i][key]  = value_replace
                    variable_width[key] = len(values[0])
          for key in keys_to_delete:
               del current_variables[key]
          
          name, ext = os.path.splitext(fname)
          if(is_reduce):
               self.formula_dict[os.path.basename(name)] = current_variables.copy()     
          else:
               self.formula_dict_without_reduce[os.path.basename(name)] = current_variables.copy()
          
          return variable_width
     
     def dump_to_template(self,fname):
          collect_path = "./grammar_gen_verlilog"
          if(os.path.exists(collect_path)==False):
               os.makedirs(collect_path)
          else:
               assert os.path.exists(collect_path)
               shutil.rmtree(collect_path)
               os.makedirs(collect_path) ## We need to remove the grammar that are generated previously
               
          filename = os.path.basename(fname)
          file_without_extension = os.path.splitext(filename)[0]
          path_for_fname = os.path.join(collect_path,file_without_extension)

          # if(os.path.exists(path_for_fname)==False):
          #      os.makedirs(path_for_fname)
          
          assert os.path.exists("./grammar/template.sl")
          with open("./grammar/template.sl", 'r') as file:
               lines = file.read()
          for formula, data_all in self.formula_dict.items():
               name, ext = os.path.splitext(path_for_fname)
               template_file = name + ".sl"
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
          return collect_path          
     

     
     
     def generate_fault_pattern(self,variables, combination, current_variable_index, index):
          if(index in self.fault_pattern):
               if(len(self.fault_pattern[index])>800):
                    return
          if current_variable_index == len(variables):
               count = 0
               flag = 0
               for key, value in self.combinations_dict.items():
                    count += 1
                    if value == combination:
                         # print(f"查询到组合 {key}: {combination}")
                         flag = 1
                         break
               if((count == len(self.combinations_dict)) and flag == 0):
                    combination_copy = combination.copy()
                    if(index in self.fault_pattern):
                         self.fault_pattern[index] = self.fault_pattern[index] + [combination_copy]
                    else:
                         self.fault_pattern[index] = [combination_copy]
          else:
               variable = list(variables.keys())[current_variable_index]
               num_bits = variables[variable]
               for value in range(2 ** num_bits):
                    combination[variable] = f"{value:0{num_bits}b}"
                    self.generate_fault_pattern(variables, combination, current_variable_index + 1,index)
 

     
     def S2Vgraph(self,device):
          for formula, data_all in self.formula_dict.items():
               self.formula_dict_tensor[formula] = {}
               # if(formula =='(= t (bvor (bvand x y) z))_1'):
               #      print(formula)
               for var in data_all:
                    numeric_list = [[[int(string, 2),len(string)]] for string in data_all[var]]
                    self.formula_dict_tensor[formula][var] = torch.tensor(numeric_list, dtype=torch.float).squeeze(1).to(device)

     def static_analysis_mask(self,current_formula):

          # 用于存储找到的 .btor 文件
          btor_files = []

          # 遍历文件夹中的文件
          for filename in os.listdir(cmd_args.data_root):
               if filename.endswith('.btor') or filename.endswith('.btor2'):
                    btor_files.append(filename)
          
          assert len(btor_files) == 1, f"Found {len(btor_files)} .btor files instead of 1."
          consts_dict = {}
          with open(os.path.join(cmd_args.data_root,btor_files[0]), 'r') as file:
               lines = file.readlines()
          for line in lines:
                    # 检查这一行是否包含"const"
               if('constd' in line):
                    words = line.split()
                    # 获取最后一个元素
                    last_word = words[-1]                    
                    index = int(words[-2])
                    parts = lines[index].split()
                    width = parts[-1]
                    assert width.isdigit()
                    binary_string = bin(int(last_word))[2:]
                    int_width = int(width)
                    # Pad with leading zeros to the specified width
                    binary_string_padded = binary_string.zfill(int_width)      
                    assert len(binary_string_padded) == int_width
                    if int_width not in consts_dict:
                         consts_dict[int_width] = [binary_string_padded]
                    else:
                         consts_dict[int_width].append(binary_string_padded)                                  
               elif 'const' in line:
                    # 分割行以获取单词列表
                    words = line.split()
                    # 获取最后一个元素
                    last_word = words[-1]
                    # 将结果存入字典，key是"const"的长度
                    if len(last_word) not in consts_dict:
                         consts_dict[len(last_word)] = [last_word]
                    else:
                         consts_dict[len(last_word)].append(last_word)
          
          self.cand_masking[current_formula] = consts_dict

     def static_analysis_add_sub(self,dic_value,current_formula):
          # 获取每个变量的位宽
          bit_widths = {key: len(dic_value[key][0]) for key in dic_value}

          # 根据位宽将变量分组
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
                         self.cand_const_add[current_formula] =dict_eq.copy()
                         self.cand_const_sub[current_formula] =dict_eq.copy()
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
                         # result_add.append(bitwise_addition(dic_value[key_combination[0]][i],dic_value[key_combination[1]][i]))
                         candidate_1 = bitwise_subtraction(dic_value[key_combination[0]][i],dic_value[key_combination[1]][i])
                         candidate_2 = bitwise_subtraction(dic_value[key_combination[1]][i],dic_value[key_combination[0]][i])
                         result_add.append(candidate_1)
                         result_add.append(candidate_2)
                         result_sub.append(candidate_1)
                         result_sub.append(candidate_2)
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
                         self.cand_const_add[current_formula][key] = value
               else:
                    self.cand_const_add[current_formula] = cand_const_add_single_reduce
               if(current_formula in self.cand_const_sub):
                    for key,value in cand_const_sub_single_reduce.items():
                         assert key not in self.cand_const_sub[current_formula]
                         self.cand_const_sub[current_formula][key] = value               
               else:
                    self.cand_const_sub[current_formula] = cand_const_sub_single_reduce
          assert self.cand_const_sub == self.cand_const_add
if __name__ == "__main__":
     path = "/data/zhiyuany/property_mining/SP.txt"
     data_smt = data_from_verilog()
     data_smt.load_verilog(path)
     for formula, data_all in data_smt.formula_dict.items():
          print(f"{formula}:")
          for var in data_all:
               print(var,data_all[var])
     data_smt.dump_to_template(path)