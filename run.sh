arg1="$1"
arg2="$2"
arg3="$3"
arg4="$4"
arg5="$5"
python3 run.py -data_root $arg1 \
               -num_epochs 250 \
               -eps 0.85 \
               -rl_batchsize 1 \
               -data_path /data/zhiyuany/property_mining/test_case/SP/SP.txt \
               -seed 1\
               -iteration $arg2\
               -exit_on_find $arg3 \
               -solution_path mining_collection\
               -tune_test 1\
               -tune_test_encoder $arg4\
               -tune_test_decoder $arg5\
               -use_cuda \
               -reward_result_path data_collection_symbols_const_epoch_reward.txt


