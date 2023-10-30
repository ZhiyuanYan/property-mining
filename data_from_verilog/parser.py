import os
import torch
import re
# from parser_syg.sygus_parser import SyExp,match_p,separate_p

class data_from_verilog(object):
     def __init__(self):
          self.formula_dict = {}
          self.COI_variable = {}
          self.formula_dict_tensor = {}
          self.combinations_dict = {}
          self.fault_pattern = {}
          # self.using_COI = using_COI
          self.cex = {}
     
     def extract_bits(self, number_str, left_index, right_index):
          # number_str = '0101'
          # left_index = 2
          # right_index = 0
          reversed_str = number_str[::-1]
          extracted_value = reversed_str[right_index:left_index + 1][::-1]
          return extracted_value
     
     def load_verilog(self,fname):
          pattern = re.compile(r'^x+$')
          
          
          # We first parse the COI variables we got from cosa2
          assert os.path.exists("COI.txt")
          
          with open("COI.txt", 'r') as coi_file:
               lines_coi = coi_file.readlines()
          
          for line in lines_coi:
               line_info = line.strip()
               line_split = line_info.split()
               
               if(line_split[0].startswith('RTL.')==False):
                    continue
               
               var = line_split[0].replace('RTL.','')
               for i in range(int(line_split[1])):
                    left = line_split[(i+1)*2]
                    right = line_split[(i+1)*2+1]
                    if i == 0:
                         self.COI_variable[var] =[var+'['+left+':'+right+']']
                    else:
                         self.COI_variable[var].append((var+'['+left+':'+right+']'))
                    assert line_split[-1].startswith('#b')
                    value = line_split[-1].replace('#b','')
                    extracted_val = self.extract_bits(value, int(left), int(right))
                    self.cex[var+'['+left+':'+right+']'] = extracted_val
          with open(fname, 'r') as file:
               lines = file.readlines()
          # current_formula = None
          skip_first_line = True
          seen_lines = set()
          current_variables = {}
          count = 0
          comb_in_one_clcle = {}
          for line in lines:
               if line not in seen_lines:
                    # count = count + 1 
                    seen_lines.add(line)
               else:
                    # count_1 = count_1 + 1
                    continue
               
               if skip_first_line:
                    skip_first_line = False
                    continue
               
               line = line.strip()
               parts = line.split(', ')
               # count = 0
               for part in parts:
                    # count = count + 1
                    # if(count>500):
                    #      break
                    split = part.split(': ')
                    variable_name = split[0].strip()
                    if((variable_name in self.COI_variable.keys())==False):
                         continue
                    
                    value = split[1].strip()
                    for var in self.COI_variable[variable_name]:
                         match = re.search(r'\[(\d+):(\d+)\]', var)
                         assert match
                         # value ='021213223'
                         start = int(match.group(1))
                         end = int(match.group(2))
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
          self.formula_dict[os.path.basename(name)] = current_variables.copy()
          ##Now lets generate a fault pattern
          self.generate_fault_pattern(variable_width,{},0,os.path.basename(name))

     def dump_to_template(self,fname):
          collect_path = "./grammar_gen_verlilog"
          if(os.path.exists(collect_path)==False):
               os.makedirs(collect_path)
          
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


if __name__ == "__main__":
     path = "/data/zhiyuany/property_mining/SP.txt"
     data_smt = data_from_verilog()
     data_smt.load_verilog(path)
     for formula, data_all in data_smt.formula_dict.items():
          print(f"{formula}:")
          for var in data_all:
               print(var,data_all[var])
     data_smt.dump_to_template(path)