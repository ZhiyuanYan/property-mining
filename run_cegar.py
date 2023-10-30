import subprocess
import argparse
import os
from datetime import datetime

def log2fs(s,cmd_args):
    t = datetime.now()
    print(t,'--->',s)
    path = os.path.join(cmd_args.data_path,'cegar.log')
    with open(path , 'a') as fout:
        fout.write(str(t))
        fout.write(' ---> ')
        fout.write(s)    
        fout.write('\n')

def try_rm(name):
    try:
        os.remove(name)
    except:
        pass

def getiter(env_inv):
    old_num = 0
    with open(env_inv) as fin:
        for line in fin.readlines():
            #                   01234567890123456789012
            if line.startswith('(define-fun assumption.'):
                idx = line.index(' ',22)
                old_num = int(line[23:idx]) + 1
    return old_num
  



def run_cegar(cmd_args):
    ####Let's check whether the file exists###
    problem_btor = os.path.join(cmd_args.data_path,'verify/problem.btor2')
    assert os.path.exists(problem_btor)

    design_btor = os.path.join(cmd_args.data_path,'envinv/design.btor')
    assert os.path.exists(design_btor)
    env_inv = os.path.join(cmd_args.data_path,'envinv.smt2')

    ###Now let's begin the main program#####

    n_iteration = 0
    if not os.path.exists(env_inv):
        with open(env_inv,'w') as fout:
            fout.write('')
    else:
        n_iteration = getiter(env_inv)
    


    errFlag = False
    while not errFlag:
        try_rm("check.result")
        try_rm("COI.txt")
        log2fs ('running QED iter #' + str( n_iteration),cmd_args )
        subprocess.run(["./cosa2/build/cexgen","--logging-smt-solver","--property-file", env_inv,problem_btor])
        
        try:
            result = open('check.result')
        except:
            log2fs ('cexgen failed.',cmd_args)
            errFlag = True
            break
        qed_res = result.readline()
        result.close()
        del result
        
        if 'unsat' in qed_res:
            log2fs ('no more cex. CEGAR termindates.',cmd_args)
            break
        if not 'sat' in qed_res:
            log2fs ('cexgen produced unexpected result:' + qed_res,cmd_args)
            errFlag = True
            break
        if not os.path.exists("COI.txt"):
            log2fs ('cexgen didn\'t produce waveform.',cmd_args)
            errFlag = True
            break
        del qed_res
        
        # now the second part
        try_rm("check.result")
        oldsize = os.path.getsize(env_inv)
        
        encoder = os.path.join(cmd_args.data_path, 'mem_encoder')
        decoder = os.path.join(cmd_args.data_path, 'decoder')
        if os.path.exists(encoder)==False:
            assert os.path.exists(decoder)==False
            encoder = cmd_args.init_encoder
            decoder = cmd_args.init_decoder
            
        log2fs('running property mining #'+str(n_iteration),cmd_args)   
        
        subprocess.run(["bash","run.sh", cmd_args.data_path,str(n_iteration),str(1),encoder,decoder])
        
        path_mining_result = os.path.join(cmd_args.data_path,"result.txt")
        try:
            result = open(path_mining_result)
        except:
            log2fs ('property mining failed.',cmd_args)
            errFlag = True
            break
        syn_res = result.readline()
        result.close()
        del result
        
        if 'find_assumption' not in syn_res:
            log2fs ('mining process produced unexpected result:' + syn_res,cmd_args)
            errFlag = True
            break
        # else:
        #     path = os.path.join(cmd_args.data_path, 'smt_lib2/' + str(oldsize))    
        #     file_count = len([f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))])
        #     assertion_path = os.path.join(path,'assertion' + str(file_count) + '.smt2')
        #     with open(assertion_path, 'r') as source_file:
        #         content = source_file.read()
        #     content = content.replace("assertion", "assumption")
        #     with open(env_inv, 'w') as destination_file:
        #         destination_file.write(content)

        newsize = os.path.getsize(env_inv)
        if not (newsize > oldsize):
            log2fs ('envinv size is strange! ' + str(oldsize) + ' ---> ' + str(newsize),cmd_args)
            errFlag = True
            break
        log2fs('finish iter #'+str(n_iteration),cmd_args)
        n_iteration += 1


if __name__ == '__main__':
    cmd_opt = argparse.ArgumentParser(description='Argparser')
    cmd_opt.add_argument('-data_path', default=None, help='root of the design and its subfolders')
    cmd_opt.add_argument('-init-encoder', default=None, help='the pretrained encoder.')
    cmd_opt.add_argument('-init-decoder', default=None, help='the pretrained decoder.')
    cmd_args, _ = cmd_opt.parse_known_args()
    run_cegar(cmd_args)