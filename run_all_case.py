import os 
import argparse
import subprocess
import threading
import signal
import errno
from multiprocessing import Pool, Manager
from functools import partial
import shutil
from itertools import combinations
import time


global_pids = []

def print_output(stream):
    for line in iter(stream.readline, b''):
        print(line, end='')

def terminate_process_group(pid):
    try:
        os.killpg(os.getpgid(pid), signal.SIGTERM)
    except OSError as e:
        if e.errno != errno.ESRCH:
            raise

def create_combinations_folder(src_folder, max_files=5):
    assertion_path = os.path.join(src_folder,"assertion")
    files = [f for f in os.listdir(assertion_path) if os.path.isfile(os.path.join(assertion_path, f))]

    # if len(files) > max_files:
    #     print(f"Folder has more than {max_files} files. Exiting.")
    #     return
    folder_collect = []
    if len(files) <= 2:
        for i, file in enumerate(files, 1):
            new_folder = os.path.join(src_folder, f"single_{i}")
            os.makedirs(new_folder, exist_ok=True)
            shutil.copy(os.path.join(assertion_path, file), new_folder)
            folder_collect.append(new_folder)
        if len(files) == 2:
            new_folder = os.path.join(src_folder, "combo")
            os.makedirs(new_folder, exist_ok=True)
            for file in files:
                shutil.copy(os.path.join(assertion_path, file), new_folder)
            folder_collect.append(new_folder)

    else:
        # combo_num = 2 if len(files) > 2 else 1
        for i, combo in enumerate(combinations(files, 2), 1):
            new_folder = os.path.join(src_folder, f"combo_2_{i}")
            os.makedirs(new_folder, exist_ok=True)
            for file in combo:
                shutil.copy(os.path.join(assertion_path, file), new_folder)
            folder_collect.append(new_folder)        

        for i, combo in enumerate(combinations(files, 3), 1):
            new_folder = os.path.join(src_folder, f"combo_3_{i}")
            os.makedirs(new_folder, exist_ok=True)
            for file in combo:
                shutil.copy(os.path.join(assertion_path, file), new_folder)
            folder_collect.append(new_folder)  
    return folder_collect

def run_mining(command_to_run):
    
    process = subprocess.Popen(
        command_to_run,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid  # 用于设置会话ID，创建新的进程组
    )
    try:
        # 等待子进程完成或超时
        stdout, stderr = process.communicate(timeout=600)
        # 这里根据实际需求处理输出
        if stderr:  # 如果存在标准错误输出
            print("Error detected. STDERR:\n", stderr)
            # 这里可以根据错误内容决定是否处理或退出
            return "Error"
        return stdout.deocde()
    except subprocess.TimeoutExpired:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        # process.kill()
        stdout, stderr = process.communicate()
        print("Process timed out. STDOUT:\n", stdout)
        print("STDERR:\n", stderr)
        return "Timeout"

def run_pono(folder_name, btor_file, status_dict):
    global global_pids
    command_to_run_pono = ["./build/pono", "--assertion-folder", folder_name,
                           "-e", "ic3bits", "--bound", "1000", "--print-wall-time", btor_file]

    process = subprocess.Popen(command_to_run_pono, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # global_pids.append(process.pid)

    start_time = time.time()  # Record the start time
    try:
        while True:
            # Check if the process has ended or if a termination signal is set
            if process.poll() is not None or status_dict.get('terminate', False):
                break

            # Check if the timeout has been exceeded
            elapsed_time = time.time() - start_time
            if elapsed_time > 3600:  # 3600 seconds = 1 hour
                status_dict['terminate'] = True
                process.kill()
                break

            # Wait for some time before checking again
            time.sleep(0.5)  # Adjust the sleep time as needed

        stdout, stderr = process.communicate(timeout=1)  # Short timeout for final communication
        return stdout.decode(), process.pid, command_to_run_pono
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()
        return stdout.decode(), process.pid, command_to_run_pono

def is_folder_empty(folder_path):
    """Check if a folder is empty."""
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        return not os.listdir(folder_path)
    else:
        raise ValueError("Provided path is not a valid folder")

def run_pono_single(command_to_run_pono):
    process = subprocess.Popen(command_to_run_pono, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    global_pids.append(process.pid)
    try:
        stdout, stderr = process.communicate(timeout=3600)
        return stdout.decode()
    except subprocess.TimeoutExpired:
        process.kill()
        
        stdout, stderr = process.communicate()
        return stdout.decode()


def terminate_all_pids():
    global global_pids
    for pid in global_pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError as e:
            print(f"Error terminating process {pid}: {e}")
    global_pids = []

def run_all_cases(path):
        assert os.path.isdir(path)
        btor_files = []
        print("Now running on the case: %s\n"%(path))
        for filename in os.listdir(path):
               btor_path = os.path.join(path,filename)
               if filename.endswith('.btor') or filename.endswith('.btor2'):
                    btor_files.append(btor_path)
          
        assert len(btor_files) == 1, f"Found {len(btor_files)} .btor files instead of 1."
        data_path = os.path.join(path,'verilog/test.txt')
        command_to_run_mining = ["bash", "run_mining.sh",path,
            data_path
            ]
        time_start = time.time()
        std_out = run_mining(command_to_run_mining)
        time_end = time.time()
        print("The mining time is: %.4f"%(time_end-time_start))
        subfolder_name = "assertion"
        print("Now running on pono: %s"%(path))
        
        out = None
        command = None
        def on_complete(result):
            nonlocal out
            nonlocal command 
            if out is None: 
                out = result[0]
                command = result[2]
            print(f"Process complete with result: {result[0]}")
            
            pool.terminate() 
            # for folder in divided_path:
            #     if os.path.exists(folder):
            #         shutil.rmtree(folder)
        assertion_path = os.path.join(path,subfolder_name)
        if subfolder_name in os.listdir(path) and is_folder_empty(assertion_path)==False:
            # assertion_path = os.path.join(path,subfolder_name)
            manager = Manager()
            status_dict = manager.dict()
            status_dict['terminate'] = False

            pool = Pool(processes=20)
            divided_path = create_combinations_folder(path, max_files=5)
            for folder in divided_path:
                if status_dict.get('terminate', False):
                    break  # Stop creating new processes if termination signal is set
                pool.apply_async(run_pono, args=(folder, btor_files[0], status_dict), callback=on_complete)

            pool.close()
            pool.join()
            try:
                # Recheck if the process is running
                # process_check_output = subprocess.getoutput(process_check_command)

                # If the process is found, execute the kill command
                # if "./cosa2/build/pono --assertion-folder" in process_check_output:
                    subprocess.run(["pkill", "-f", "./cosa2/build/pono --assertion-folder"], check=True)
                    # kill_result = "Kill command executed successfully."
                # else:
                    # kill_result = "No matching process found, no action taken."

            except subprocess.CalledProcessError as e:
                # If there's an error (such as process not found), handle it here
                kill_result = f"An error occurred: {e}"
                
                # terminate_all_pids()
        else:
            command_to_run_pono = ["./cosa2/build/pono", "--bound","1000",
            "-e","ic3bits",
            "--print-wall-time",
            btor_files[0]
            ]            
            out = run_pono_single(command_to_run_pono)
        with open(cmd_args.logging, 'a+') as file:
            file.write(path+"\n")
            file.write("The mining time is: %.4f\n"%(time_end-time_start))
            if("unsat" in out):
                print("Successful: %s"%(path))
                if(command is not None):
                    file.write(out+"\n" + command[2] + "\n")
                else:
                    file.write(out + "\n")
            else:
                print("Unsuccessful: %s"%(path))
                file.write("This cannot be checked\n")                
                
if __name__ == '__main__':
    cmd_opt = argparse.ArgumentParser(description='Argparser')
    cmd_opt.add_argument('-data_path', default=None, help='root of the all cases')
    cmd_opt.add_argument('-logging', default=None, help='the logging infomation of the output.')
    # cmd_opt.add_argument('-init-decoder', default=None, help='the pretrained decoder.')
    cmd_args, _ = cmd_opt.parse_known_args()
    file_list = []
    for file_folder in os.listdir(cmd_args.data_path):
        path = os.path.join(cmd_args.data_path,file_folder)
        run_all_cases(path)
    #     file_list.append(path)
    # pool = Pool(processes=1)  
    # # ex_pono_partisal = partial(run_all_cases)
    # pool.map(run_all_cases, file_list)
    # pool.close()
    # pool.join()        

