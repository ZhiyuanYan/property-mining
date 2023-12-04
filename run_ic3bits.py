import os 
import argparse
import subprocess
import time
from multiprocessing import Pool
from functools import partial
def run_pono(commond_to_run):
    process = subprocess.Popen(commond_to_run, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        stdout, stderr = process.communicate(timeout=3600)
        return stdout.decode()
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()
        return stdout.decode()


def run_all_cases(path):
        assert os.path.isdir(path)
        btor_files = []
        print("Now running on the case: %s\n"%(path))
        for filename in os.listdir(path):
               btor_path = os.path.join(path,filename)
               if filename.endswith('.btor') or filename.endswith('.btor2'):
                    btor_files.append(btor_path)
          
        assert len(btor_files) == 1, f"Found {len(btor_files)} .btor files instead of 1."
        data_path = os.path.join(path,btor_files[0])
        command_to_run_pono = ["./cosa2/build/pono", "--bound","1000",
        "-e","ic3bits",
        "--print-wall-time",
        btor_files[0]
        ]   
        time_start = time.time()
        std_out =run_pono(command_to_run_pono)
        time_end = time.time()
        print("The solving time is: %.4f"%(time_end-time_start))
        with open(cmd_args.logging, 'a+') as file:
            file.write(path+"\n")
            file.write("The solving time is: %.4f\n"%(time_end-time_start))
            file.write(std_out+"\n")
            # if("unsat" in out):
            #     print("Successful: %s"%(path))
            #     file.write(out+"\n")
            # else:
            #     print("Unsuccessful: %s"%(path))
            #     file.write("This cannot be checked\n")         
        
if __name__ == '__main__':
    cmd_opt = argparse.ArgumentParser(description='Argparser')
    cmd_opt.add_argument('-data_path', default=None, help='root of the all cases')
    cmd_opt.add_argument('-logging', default=None, help='the logging infomation of the output.')
    # cmd_opt.add_argument('-init-decoder', default=None, help='the pretrained decoder.')
    cmd_args, _ = cmd_opt.parse_known_args()
    file_list = []
    for file_folder in os.listdir(cmd_args.data_path):
        path = os.path.join(cmd_args.data_path,file_folder)
        file_list.append(path)
        # run_all_cases(path)

    pool = Pool(processes=10)  
    # ex_pono_partisal = partial(ex_pono, logging_failure=logging_failure, logging_coi=logging_coi, logging_pivot_input=logging_pivot_input)
    pool.map(run_all_cases, file_list)
    pool.close()
    pool.join()
    