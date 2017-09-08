#!/bin/bash

# remember to update the compiled train:
# NB: directory where program is run (PATH_TO/fbcode) matters
# buck build @mode/opt -c fbcode.platform=gcc-4.9-glibc-2.20 experimental/commai/env/src:train
# cp ~/fbsource/fbcode/buck-out/gen/experimental/commai/env/src/train.par /mnt/vol/gfsai-flash-east/ai-group/users/mbaroni/lookup_experiments/

# NB: paths might have to be updated to the flash/non-flash directory!!!

# also, the relevant config files must be copied to the directory above

# COMPOSITIONAL
echo compositional 1

exp_name="3bit_up_to_3_eight_1_compositional"
temp_dir="/tmp/$exp_name"
config_file="tasks_config.3bit_up_to_3_eight_1_compositional.json"
my_processes="mkdir $temp_dir;
cp /mnt/vol/gfsai-flash-east/ai-group/users/mbaroni/lookup_experiments/train.par $temp_dir;
cp /mnt/vol/gfsai-flash-east/ai-group/users/mbaroni/lookup_experiments/$config_file $temp_dir;
OMP_NUM_THREADS=1 $temp_dir/train.par $temp_dir/$config_file --learner experimental.learner.BlockControlGraphLearner -s core.serializer.IdentitySerializer --max-reward-per-task 50000000000 --err_debug True --ponder_env True --view experimental.view.View --nhid 150 --sparcity 0 --dropout 0 --nreplay 1 --entropy_reg 0.1 --lr 1e-3 --gamma 0.99 --Cblock 10 --rnntype LSTM --log_interval 1000 --exp_name ${exp_name}_ --log_dir $temp_dir --num_processes 10 --output $temp_dir/${exp_name}_outfile --vis_interval 100;
cp -r $temp_dir /mnt/vol/gfsai-east/ai-group/users/mbaroni/lookup_experiments;"

echo "$my_processes" | crun -G 0 -C 10 -M 40 --retries 3 --hostgroup fblearner_ash_cpuram_default -

echo compositional 2

exp_name="3bit_up_to_3_eight_2_compositional"
temp_dir="/tmp/$exp_name"
config_file="tasks_config.3bit_up_to_3_eight_2_compositional.json"
my_processes="mkdir $temp_dir;
cp /mnt/vol/gfsai-flash-east/ai-group/users/mbaroni/lookup_experiments/train.par $temp_dir;
cp /mnt/vol/gfsai-flash-east/ai-group/users/mbaroni/lookup_experiments/$config_file $temp_dir;
OMP_NUM_THREADS=1 $temp_dir/train.par $temp_dir/$config_file --learner experimental.learner.BlockControlGraphLearner -s core.serializer.IdentitySerializer --max-reward-per-task 50000000000 --err_debug True --ponder_env True --view experimental.view.View --nhid 150 --sparcity 0 --dropout 0 --nreplay 1 --entropy_reg 0.1 --lr 1e-3 --gamma 0.99 --Cblock 10 --rnntype LSTM --log_interval 1000 --exp_name ${exp_name}_ --log_dir $temp_dir --num_processes 10 --output $temp_dir/${exp_name}_outfile --vis_interval 100;
cp -r $temp_dir /mnt/vol/gfsai-east/ai-group/users/mbaroni/lookup_experiments;"

echo "$my_processes" | crun -G 0 -C 10 -M 40 --retries 3 --hostgroup fblearner_ash_cpuram_default -

echo compositional 3

exp_name="3bit_up_to_3_eight_3_compositional"
temp_dir="/tmp/$exp_name"
config_file="tasks_config.3bit_up_to_3_eight_3_compositional.json"
my_processes="mkdir $temp_dir;
cp /mnt/vol/gfsai-flash-east/ai-group/users/mbaroni/lookup_experiments/train.par $temp_dir;
cp /mnt/vol/gfsai-flash-east/ai-group/users/mbaroni/lookup_experiments/$config_file $temp_dir;
OMP_NUM_THREADS=1 $temp_dir/train.par $temp_dir/$config_file --learner experimental.learner.BlockControlGraphLearner -s core.serializer.IdentitySerializer --max-reward-per-task 50000000000 --err_debug True --ponder_env True --view experimental.view.View --nhid 150 --sparcity 0 --dropout 0 --nreplay 1 --entropy_reg 0.1 --lr 1e-3 --gamma 0.99 --Cblock 10 --rnntype LSTM --log_interval 1000 --exp_name ${exp_name}_ --log_dir $temp_dir --num_processes 10 --output $temp_dir/${exp_name}_outfile --vis_interval 100;
cp -r $temp_dir /mnt/vol/gfsai-east/ai-group/users/mbaroni/lookup_experiments;"

echo "$my_processes" | crun -G 0 -C 10 -M 40 --retries 3 --hostgroup fblearner_ash_cpuram_default -

echo compositional 4

exp_name="3bit_up_to_3_eight_4_compositional"
temp_dir="/tmp/$exp_name"
config_file="tasks_config.3bit_up_to_3_eight_4_compositional.json"
my_processes="mkdir $temp_dir;
cp /mnt/vol/gfsai-flash-east/ai-group/users/mbaroni/lookup_experiments/train.par $temp_dir;
cp /mnt/vol/gfsai-flash-east/ai-group/users/mbaroni/lookup_experiments/$config_file $temp_dir;
OMP_NUM_THREADS=1 $temp_dir/train.par $temp_dir/$config_file --learner experimental.learner.BlockControlGraphLearner -s core.serializer.IdentitySerializer --max-reward-per-task 50000000000 --err_debug True --ponder_env True --view experimental.view.View --nhid 150 --sparcity 0 --dropout 0 --nreplay 1 --entropy_reg 0.1 --lr 1e-3 --gamma 0.99 --Cblock 10 --rnntype LSTM --log_interval 1000 --exp_name ${exp_name}_ --log_dir $temp_dir --num_processes 10 --output $temp_dir/${exp_name}_outfile --vis_interval 100;
cp -r $temp_dir /mnt/vol/gfsai-east/ai-group/users/mbaroni/lookup_experiments;"

echo "$my_processes" | crun -G 0 -C 10 -M 40 --retries 3 --hostgroup fblearner_ash_cpuram_default -

echo compositional 5

exp_name="3bit_up_to_3_eight_5_compositional"
temp_dir="/tmp/$exp_name"
config_file="tasks_config.3bit_up_to_3_eight_5_compositional.json"
my_processes="mkdir $temp_dir;
cp /mnt/vol/gfsai-flash-east/ai-group/users/mbaroni/lookup_experiments/train.par $temp_dir;
cp /mnt/vol/gfsai-flash-east/ai-group/users/mbaroni/lookup_experiments/$config_file $temp_dir;
OMP_NUM_THREADS=1 $temp_dir/train.par $temp_dir/$config_file --learner experimental.learner.BlockControlGraphLearner -s core.serializer.IdentitySerializer --max-reward-per-task 50000000000 --err_debug True --ponder_env True --view experimental.view.View --nhid 150 --sparcity 0 --dropout 0 --nreplay 1 --entropy_reg 0.1 --lr 1e-3 --gamma 0.99 --Cblock 10 --rnntype LSTM --log_interval 1000 --exp_name ${exp_name}_ --log_dir $temp_dir --num_processes 10 --output $temp_dir/${exp_name}_outfile --vis_interval 100;
cp -r $temp_dir /mnt/vol/gfsai-east/ai-group/users/mbaroni/lookup_experiments;"

echo "$my_processes" | crun -G 0 -C 10 -M 40 --retries 3 --hostgroup fblearner_ash_cpuram_default -

# CONTROL
echo control 1

exp_name="3bit_up_to_3_eight_1_control"
temp_dir="/tmp/$exp_name"
config_file="tasks_config.3bit_up_to_3_eight_1_control.json"
my_processes="mkdir $temp_dir;
cp /mnt/vol/gfsai-flash-east/ai-group/users/mbaroni/lookup_experiments/train.par $temp_dir;
cp /mnt/vol/gfsai-flash-east/ai-group/users/mbaroni/lookup_experiments/$config_file $temp_dir;
OMP_NUM_THREADS=1 $temp_dir/train.par $temp_dir/$config_file --learner experimental.learner.BlockControlGraphLearner -s core.serializer.IdentitySerializer --max-reward-per-task 50000000000 --err_debug True --ponder_env True --view experimental.view.View --nhid 150 --sparcity 0 --dropout 0 --nreplay 1 --entropy_reg 0.1 --lr 1e-3 --gamma 0.99 --Cblock 10 --rnntype LSTM --log_interval 1000 --exp_name ${exp_name}_ --log_dir $temp_dir --num_processes 10 --output $temp_dir/${exp_name}_outfile --vis_interval 100;
cp -r $temp_dir /mnt/vol/gfsai-east/ai-group/users/mbaroni/lookup_experiments;"

echo "$my_processes" | crun -G 0 -C 10 -M 40 --retries 3 --hostgroup fblearner_ash_cpuram_default -

echo control 2

exp_name="3bit_up_to_3_eight_2_control"
temp_dir="/tmp/$exp_name"
config_file="tasks_config.3bit_up_to_3_eight_2_control.json"
my_processes="mkdir $temp_dir;
cp /mnt/vol/gfsai-flash-east/ai-group/users/mbaroni/lookup_experiments/train.par $temp_dir;
cp /mnt/vol/gfsai-flash-east/ai-group/users/mbaroni/lookup_experiments/$config_file $temp_dir;
OMP_NUM_THREADS=1 $temp_dir/train.par $temp_dir/$config_file --learner experimental.learner.BlockControlGraphLearner -s core.serializer.IdentitySerializer --max-reward-per-task 50000000000 --err_debug True --ponder_env True --view experimental.view.View --nhid 150 --sparcity 0 --dropout 0 --nreplay 1 --entropy_reg 0.1 --lr 1e-3 --gamma 0.99 --Cblock 10 --rnntype LSTM --log_interval 1000 --exp_name ${exp_name}_ --log_dir $temp_dir --num_processes 10 --output $temp_dir/${exp_name}_outfile --vis_interval 100;
cp -r $temp_dir /mnt/vol/gfsai-east/ai-group/users/mbaroni/lookup_experiments;"

echo "$my_processes" | crun -G 0 -C 10 -M 40 --retries 3 --hostgroup fblearner_ash_cpuram_default -

echo control 3

exp_name="3bit_up_to_3_eight_3_control"
temp_dir="/tmp/$exp_name"
config_file="tasks_config.3bit_up_to_3_eight_3_control.json"
my_processes="mkdir $temp_dir;
cp /mnt/vol/gfsai-flash-east/ai-group/users/mbaroni/lookup_experiments/train.par $temp_dir;
cp /mnt/vol/gfsai-flash-east/ai-group/users/mbaroni/lookup_experiments/$config_file $temp_dir;
OMP_NUM_THREADS=1 $temp_dir/train.par $temp_dir/$config_file --learner experimental.learner.BlockControlGraphLearner -s core.serializer.IdentitySerializer --max-reward-per-task 50000000000 --err_debug True --ponder_env True --view experimental.view.View --nhid 150 --sparcity 0 --dropout 0 --nreplay 1 --entropy_reg 0.1 --lr 1e-3 --gamma 0.99 --Cblock 10 --rnntype LSTM --log_interval 1000 --exp_name ${exp_name}_ --log_dir $temp_dir --num_processes 10 --output $temp_dir/${exp_name}_outfile --vis_interval 100;
cp -r $temp_dir /mnt/vol/gfsai-east/ai-group/users/mbaroni/lookup_experiments;"

echo "$my_processes" | crun -G 0 -C 10 -M 40 --retries 3 --hostgroup fblearner_ash_cpuram_default -

echo control 4

exp_name="3bit_up_to_3_eight_4_control"
temp_dir="/tmp/$exp_name"
config_file="tasks_config.3bit_up_to_3_eight_4_control.json"
my_processes="mkdir $temp_dir;
cp /mnt/vol/gfsai-flash-east/ai-group/users/mbaroni/lookup_experiments/train.par $temp_dir;
cp /mnt/vol/gfsai-flash-east/ai-group/users/mbaroni/lookup_experiments/$config_file $temp_dir;
OMP_NUM_THREADS=1 $temp_dir/train.par $temp_dir/$config_file --learner experimental.learner.BlockControlGraphLearner -s core.serializer.IdentitySerializer --max-reward-per-task 50000000000 --err_debug True --ponder_env True --view experimental.view.View --nhid 150 --sparcity 0 --dropout 0 --nreplay 1 --entropy_reg 0.1 --lr 1e-3 --gamma 0.99 --Cblock 10 --rnntype LSTM --log_interval 1000 --exp_name ${exp_name}_ --log_dir $temp_dir --num_processes 10 --output $temp_dir/${exp_name}_outfile --vis_interval 100;
cp -r $temp_dir /mnt/vol/gfsai-east/ai-group/users/mbaroni/lookup_experiments;"

echo "$my_processes" | crun -G 0 -C 10 -M 40 --retries 3 --hostgroup fblearner_ash_cpuram_default -

echo control 5

exp_name="3bit_up_to_3_eight_5_control"
temp_dir="/tmp/$exp_name"
config_file="tasks_config.3bit_up_to_3_eight_5_control.json"
my_processes="mkdir $temp_dir;
cp /mnt/vol/gfsai-flash-east/ai-group/users/mbaroni/lookup_experiments/train.par $temp_dir;
cp /mnt/vol/gfsai-flash-east/ai-group/users/mbaroni/lookup_experiments/$config_file $temp_dir;
OMP_NUM_THREADS=1 $temp_dir/train.par $temp_dir/$config_file --learner experimental.learner.BlockControlGraphLearner -s core.serializer.IdentitySerializer --max-reward-per-task 50000000000 --err_debug True --ponder_env True --view experimental.view.View --nhid 150 --sparcity 0 --dropout 0 --nreplay 1 --entropy_reg 0.1 --lr 1e-3 --gamma 0.99 --Cblock 10 --rnntype LSTM --log_interval 1000 --exp_name ${exp_name}_ --log_dir $temp_dir --num_processes 10 --output $temp_dir/${exp_name}_outfile --vis_interval 100;
cp -r $temp_dir /mnt/vol/gfsai-east/ai-group/users/mbaroni/lookup_experiments;"

echo "$my_processes" | crun -G 0 -C 10 -M 40 --retries 3 --hostgroup fblearner_ash_cpuram_default -

echo done launching jobs
