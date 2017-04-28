#!/bin/bash
buck build @mode/opt -c fbcode.platform=gcc-4.9-glibc-2.20  experimental/germank/ai-challenge/src:train

lexpath=/mnt/vol/gfsai-east/ai-group/users/rchaabouni/lars/$(date +%s)
mkdir "$lexpath"
lexpath=$lexpath/train.par
echo "Copying par to $lexpath"
sudo cp -r ~/fbsource/fbcode/buck-out/gen/experimental/germank/ai-challenge/src/train.par "$lexpath"


task_dir="/mnt/vol/gfsai-east/ai-group/users/rchaabouni/commai/task_configs"
log_dir="/mnt/vol/gfsai-east/ai-group/users/rchaabouni/commai/logs"
for N in {1..10}
do
  for task_config in tasks_config.small_comp.revrot.json #\
    #tasks_config.small_comp2.json \
    #tasks_config.rotate_short.json tasks_config.rotrev_seq_parallel.json \
    #tasks_config.concatenate_short.json \
    #tasks_config.repeat_short.json \
    #tasks_config.reverse_short.json tasks_config.rotate_short.json
  do
    for lr in 3e-3 #2e-4 #8e-4
    do
      for nhid in 300 #100
      do
        for nreplay in 5 #2 10 #'cosine' 'smoothl1'
        do

          name="2_RNN_commai_comp_${task_config}_lr${lr}_nh${nhid}_nr${nreplay}_t${N}"
          str="
rsync --progress ${lexpath} . || exit 1; rsync --progress ${task_dir}/${task_config} . || exit 1; echo 'starting job';
$lexpath ${task_dir}/${task_config}  \
--learner experimental.baselines.lstm_reinforce.Learner   \
-s core.serializer.IdentitySerializer \
--max-reward-per-task 5000   \
--err_debug True --view experimental.view.View \
--nhid $nhid  --lr $lr   --gamma 0.99 \
--rnntype RNN --log_interval 200 \
--exp_name ${name} --log_dir ${log_dir} \
--nreplay ${nreplay}  --ceiling ceiling "

          # echo $str
          echo "$str" | crun -G 0 -C 10 -M 40 --retries 3 --name  ${name} --hostgroup fblearner_ash_cpuram_default -
          # exit 1
        done
      done
    done
  done
done


# ./groundsent.par --skipthought 0 --method cap2both --name ${name} --batch_size ${batch_size} --batchnorm 0 --lstm_dim 2048  --max_norm 5 --loss ${loss}
