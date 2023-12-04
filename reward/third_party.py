import os
from common.cmd_args import cmd_args
import subprocess 
import re

def run_pono(num_bnd):
    design_btor = os.path.join(cmd_args.data_root,'envinv/design.btor')
    assert os.path.exists(design_btor)
    path_folder = os.path.join(cmd_args.data_root,'assertion')
    # path = os.path.join(path_folder,str(cmd_args.iteration))
    file_count = len([f for f in os.listdir(path_folder) if os.path.isfile(os.path.join(path_folder, f))])
    assertion_path = os.path.join(path_folder,'assertion' + str(file_count-1) + '.smt2')
    assert os.path.isfile(assertion_path)
    command_to_run = ["./cosa2/build/pono", "--bound",str(num_bnd+50),
                #   "--check-invar",
                "-e", "bmc",
                "--property-file",assertion_path,
                design_btor
                ]
    print(" Running the formal check\n")
    process = subprocess.Popen(command_to_run, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        stdout, stderr = process.communicate(timeout=180)
        if('unknown' not in stdout.decode()):
            print("The potential solution is not passed by BMC ") 
            os.remove(assertion_path)
        else:    
            print(stdout.decode()) 
        return stdout.decode(),assertion_path
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()
        # raise TimeoutError("Running time out error.")
        return "unknown",assertion_path

def check_boolector(smt2,var_all,var_value,prefix=''):
    filename =  os.path.join(cmd_args.data_root,'boolector_check.smt2')
    with open(filename, 'w') as f:
        f.write(smt2 + "\n")
        var_repeat = []
        for var in var_all:
            if(var in var_repeat):
                    continue
            var_repeat.append(var)
            if('const' in var):
                    continue
            elif(var.isdigit()):
                    continue     
            if(cmd_args.use_smt_switch):
                f.write('(' + "declare-const " + prefix + var + ' ' + '(_ BitVec ' + str(len(var_value[var][0])) + ')' + ') ')
                f.write('\n')                
            else:
                match = re.match(r'(.*)(\[\d+:\d+\])$', var)
                assert match
                variable_name = match.group(1)
                f.write('(' + "declare-const "+ "|" + prefix + variable_name + "|" + ' ' + '(_ BitVec ' + str(len(var_value[var][0])) + ')' + ') ')
                f.write('\n')               
        
        f.write("(assert (not (assertion." + str(cmd_args.iteration))
        var_repeat = []
        for var in var_all:
            if(var in var_repeat):
                continue
            var_repeat.append(var)
            if('const' in var):
                continue
            elif(var.isdigit()):
                continue
            if(cmd_args.use_smt_switch):
                f.write(" ")
                f.write(var)
            else:
                match = re.match(r'(.*)(\[\d+:\d+\])$', var)
                assert match
                variable_name = match.group(1)
                f.write(" ")
                f.write( "|" + prefix + variable_name + "|")
        f.write(")))\n")
        f.write("(check-sat)") 
    
    assert os.path.exists(filename)
    command_to_run = ["./boolector/build/bin/boolector", 
            filename,
            ]    
    print(" Running the boolector\n")
    process = subprocess.Popen(command_to_run, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        stdout, stderr = process.communicate(timeout=3600)

        print(stdout.decode()) 
        return stdout.decode()
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()
        raise TimeoutError("Running time out error.")

def main():
    run_pono()