import os
import torch
from parser_syg.sygus_parser import SyExp,match_p,separate_p
class data(object):
     def __init__(self):
          self.formula_dict = {}
          self.formula_dict_label = {}
          self.formula_dict_tensor = {}
          self.formula_count = {}
     
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
          self.formula_dict[current_formula] = current_variables.copy()
          self.formula_dict_label[current_formula] = label.copy()
     
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
     data_smt = data()
     data_smt.load_smt_switch(path)
     for formula, data_all in data_smt.formula_dict.items():
          print(f"{formula}:")
          for var in data_all:
               print(var,data_all[var])
     data_smt.dump_to_template(path)