import os

class data(object):
     def __init__(self):
          self.formula_dict = {}
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
                    current_formula = line.split(":", 1)[1].strip()
                    if(current_formula == "(= (bvand x y) z)"):
                         print(current_formula)
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
               
if __name__ == "__main__":
     path = "/data/zhiyuany/property_mining/data/data_collection_symbols.txt"
     data_smt = data()
     data_smt.load_smt_switch(path)
     for formula, data_all in data_smt.formula_dict.items():
          print(f"{formula}:")
          for var in data_all:
               print(var,data_all[var])
     data_smt.dump_to_template(path)