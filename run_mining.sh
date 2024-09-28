arg1="$1"
arg2="$2"
# arg3="$3"
# arg4="$4"
# arg5="$5"
source activate metal_env
python3 run.py -data_root $arg1  \
               -num_epochs 350 \
               -eps 0.85 \
               -rl_batchsize 1 \
               -data_path $arg2 \
               -seed 1\
               -iteration 0 \
               -exit_on_find 0 \
               -solution_path mining_collection\
               -use_cuda \
               -tune_test 1\
               -tune_test_encoder ./pretraining_from_smt/mem_encoder.pth\
               -tune_test_decoder ./pretraining_from_smt/decoder.pth\
               -reward_result_path data_collection_symbols_const_epoch_reward.txt

# source activate metal_env

# python3 run.py -data_root $arg1  \
#                -num_epochs 10 \
#                -eps 0.85 \
#                -rl_batchsize 1 \
#                -data_path $arg2 \
#                -seed 1\
#                -iteration 0 \
#                -exit_on_find 0 \
#                -solution_path mining_collection\
#                -use_cuda \
#                -tune_test 0\
#                -reward_result_path data_collection_symbols_const_epoch_reward.txt