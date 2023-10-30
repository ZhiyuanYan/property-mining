import os
from common.cmd_args import cmd_args
import subprocess 

def run_pono():
    design_btor = os.path.join(cmd_args.data_root,'envinv/design.btor')
    path_folder = os.path.join(cmd_args.data_root,'assertion')
    path = os.path.join(path_folder,str(cmd_args.iteration))
    file_count = len([f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))])
    assertion_path = os.path.join(path,'assertion' + str(file_count-1) + '.smt2')
    assert os.path.isfile(assertion_path)
    command_to_run = ["./cosa2/build/pono", "--bound","20",
                  "--check-invar",
                "-e", "bmc",
                "--property-file",assertion_path,
                design_btor
                
                ]
    print(" Running the formal check\n")
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