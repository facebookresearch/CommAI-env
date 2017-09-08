#!/bin/bash

echo iteration 1
date

OMP_NUM_THREADS=1 python -m experimental.train tasks_config.np_notest_norec_cat_control_lookup_exp_1.json --learner experimental.learner.LargeGraphLearner -s core.serializer.IdentitySerializer --max-reward-per-task 50000000000 --err_debug True --view experimental.view.View --nhid 50 --sparcity 0 --dropout 0 --nreplay 1 --entropy_reg 0.01 --lr 1e-3 --gamma 0.99 --Cblock 50 --rnntype LSTM --log_interval 100 --exp_name multiprocess_np_cat_control_lookup_1_ --log_dir /home/mbaroni/fbsource/fbcode/experimental/commai/env/src/temp --num_processes 10 --output ./multiprocess_np_cat_control_lookup_log_1.out --vis_interval 100

echo iteration 2
date

OMP_NUM_THREADS=1 python -m experimental.train tasks_config.np_notest_norec_cat_control_lookup_exp_2.json --learner experimental.learner.LargeGraphLearner -s core.serializer.IdentitySerializer --max-reward-per-task 50000000000 --err_debug True --view experimental.view.View --nhid 50 --sparcity 0 --dropout 0 --nreplay 1 --entropy_reg 0.01 --lr 1e-3 --gamma 0.99 --Cblock 50 --rnntype LSTM --log_interval 100 --exp_name multiprocess_np_cat_control_lookup_2_ --log_dir /home/mbaroni/fbsource/fbcode/experimental/commai/env/src/temp --num_processes 10 --output ./multiprocess_np_cat_control_lookup_log_2.out --vis_interval 100

echo iteration 3
date

OMP_NUM_THREADS=1 python -m experimental.train tasks_config.np_notest_norec_cat_control_lookup_exp_3.json --learner experimental.learner.LargeGraphLearner -s core.serializer.IdentitySerializer --max-reward-per-task 50000000000 --err_debug True --view experimental.view.View --nhid 50 --sparcity 0 --dropout 0 --nreplay 1 --entropy_reg 0.01 --lr 1e-3 --gamma 0.99 --Cblock 50 --rnntype LSTM --log_interval 100 --exp_name multiprocess_np_cat_control_lookup_3_ --log_dir /home/mbaroni/fbsource/fbcode/experimental/commai/env/src/temp --num_processes 10 --output ./multiprocess_np_cat_control_lookup_log_3.out --vis_interval 100

echo iteration 4
date

OMP_NUM_THREADS=1 python -m experimental.train tasks_config.np_notest_norec_cat_control_lookup_exp_4.json --learner experimental.learner.LargeGraphLearner -s core.serializer.IdentitySerializer --max-reward-per-task 50000000000 --err_debug True --view experimental.view.View --nhid 50 --sparcity 0 --dropout 0 --nreplay 1 --entropy_reg 0.01 --lr 1e-3 --gamma 0.99 --Cblock 50 --rnntype LSTM --log_interval 100 --exp_name multiprocess_np_cat_control_lookup_4_ --log_dir /home/mbaroni/fbsource/fbcode/experimental/commai/env/src/temp --num_processes 10 --output ./multiprocess_np_cat_control_lookup_log_4.out --vis_interval 100

echo iteration 5
date

OMP_NUM_THREADS=1 python -m experimental.train tasks_config.np_notest_norec_cat_control_lookup_exp_5.json --learner experimental.learner.LargeGraphLearner -s core.serializer.IdentitySerializer --max-reward-per-task 50000000000 --err_debug True --view experimental.view.View --nhid 50 --sparcity 0 --dropout 0 --nreplay 1 --entropy_reg 0.01 --lr 1e-3 --gamma 0.99 --Cblock 50 --rnntype LSTM --log_interval 100 --exp_name multiprocess_np_cat_control_lookup_5_ --log_dir /home/mbaroni/fbsource/fbcode/experimental/commai/env/src/temp --num_processes 10 --output ./multiprocess_np_cat_control_lookup_log_5.out --vis_interval 100

echo done
date
