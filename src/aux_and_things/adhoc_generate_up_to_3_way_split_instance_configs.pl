#!/usr/bin/perl -w

$name_string = shift;

$composition_type = shift;

$composition_count = shift;

$lookup_table_name = shift;

$atomic_task_count = shift;

$atomic_task_episodes_count = shift;

$composed_task_train_episodes_count = shift;

$composed_task_test_episodes_count = shift;

$comp_file = "tasks_config." . $name_string . "_compositional.json";
$control_file = "tasks_config." . $name_string . "_control.json";

`rm -f $comp_file`;
`rm -f $control_file`;

open COMP,">$comp_file";
open CONTROL,">$control_file";

$preamble = << 'END_PREAMBLE';
{
  "worlds": {
    "gw": {
      "type": "worlds.grid_world.GridWorld"
    }
  },
  "tasks":
  {
END_PREAMBLE

print COMP $preamble;
print CONTROL $preamble;


@compositional_combinations = ();
@control_combinations = ();

$i=1;
while ($i<=$atomic_task_count) {
    $task_specification = << "END_TASK_SPECIFICATION";
    "LookupTaskR${composition_count}D$i": {
      "type": "tasks.micro.$lookup_table_name.LookupTaskR${composition_count}D$i"
    },
END_TASK_SPECIFICATION

    print COMP $task_specification;
    print CONTROL $task_specification;

    $control_i = $i + $atomic_task_count;
    $j=1;
    while ($j<=$atomic_task_count) {
        $control_j = $j + $atomic_task_count;
        $composed_task_specification = << "END_TASK_SPECIFICATION";
    "${composition_type}LookupTaskR${composition_count}D${i}_${j}": {
      "type": "tasks.micro.$lookup_table_name.FuncLookupTaskR${composition_count}D${i}_${j}"
    },
    "${composition_type}LookupTaskR${composition_count}D${control_i}_${control_j}": {
      "type": "tasks.micro.$lookup_table_name.FuncLookupTaskR${composition_count}D${control_i}_${control_j}"
    },
    "${composition_type}LookupTestTaskR${composition_count}D${i}_${j}": {
      "type": "tasks.micro.$lookup_table_name.FuncLookupTestTaskR${composition_count}D${i}_${j}"
    },
    "${composition_type}LookupTestTaskR${composition_count}D${control_i}_${control_j}": {
      "type": "tasks.micro.$lookup_table_name.FuncLookupTestTaskR${composition_count}D${control_i}_${control_j}"
    },
END_TASK_SPECIFICATION
        print COMP $composed_task_specification;
        print CONTROL $composed_task_specification;
        push @compositional_combinations, $i . "_" . $j;
        push @control_combinations, $control_i . "_" . $control_j;

        $k=1;
        while ($k<=$atomic_task_count) {
            $control_k = $k + $atomic_task_count;
            $composed_task_specification = << "END_TASK_SPECIFICATION";
    "${composition_type}LookupTaskR${composition_count}D${i}_${j}_${k}": {
      "type": "tasks.micro.$lookup_table_name.FuncLookupTaskR${composition_count}D${i}_${j}_${k}"
    },
    "${composition_type}LookupTaskR${composition_count}D${control_i}_${control_j}_${control_k}": {
      "type": "tasks.micro.$lookup_table_name.FuncLookupTaskR${composition_count}D${control_i}_${control_j}_${control_k}"
    },
    "${composition_type}LookupTestTaskR${composition_count}D${i}_${j}_${k}": {
      "type": "tasks.micro.$lookup_table_name.FuncLookupTestTaskR${composition_count}D${i}_${j}_${k}"
    },
    "${composition_type}LookupTestTaskR${composition_count}D${control_i}_${control_j}_${control_k}": {
      "type": "tasks.micro.$lookup_table_name.FuncLookupTestTaskR${composition_count}D${control_i}_${control_j}_${control_k}"
    },
END_TASK_SPECIFICATION
            if ($i==$atomic_task_count && $j==$atomic_task_count && $k==$atomic_task_count) {
                $composed_task_specification =~ s/,$//;
            }
            print COMP $composed_task_specification;
            print CONTROL $composed_task_specification;
            push @compositional_combinations, $i . "_" . $j . "_" . $k;
            push @control_combinations, $control_i . "_" . $control_j . "_" . $control_k;
            $k++;
        }
        $j++;
    }
    $i++;
}

$connector = << 'CONNECTOR';
  },
  "scheduler":
  {
     "type": "core.scheduler.IntervalTaskScheduler",
     "args": {
         "tasks": [
CONNECTOR
chomp $connector;
print COMP $connector;
print CONTROL $connector;

foreach $i (1..$atomic_task_count) {
    print COMP "\"LookupTaskR${composition_count}D$i\", ";
    print CONTROL "\"LookupTaskR${composition_count}D$i\", ";
}

@composed_names = ();
foreach $compositional_combination (@compositional_combinations) {
    $composed_name = "\"" . $composition_type . "LookupTaskR${composition_count}D" . $compositional_combination . "\"";
    push @composed_names,$composed_name;
}
print COMP join ", ", @composed_names;
print CONTROL join ", ", @composed_names;

print COMP ", ";
print CONTROL ", ";


@composed_test_names = ();
@control_test_names = ();
$counter=0;
while ($counter<=$#compositional_combinations) {
    $composed_test_name =  "\"" . $composition_type . "LookupTestTaskR${composition_count}D" . $compositional_combinations[$counter] . "\"";
    push @composed_test_names,$composed_test_name;
    $control_test_name = "\"" . $composition_type . "LookupTestTaskR${composition_count}D" . $control_combinations[$counter] . "\"";
    push @control_test_names,$control_test_name;
    $counter++;
}
print COMP join ", ", @composed_test_names;
print CONTROL join ", ", @control_test_names;

print COMP "\],\n         \"intervals\": \[";
print CONTROL "\],\n         \"intervals\": \[";

$begin = 0;
$end = $atomic_task_episodes_count-1;
foreach $i (1..$atomic_task_count) {
    print COMP "\[" . $begin . "," . $end . "\], ";
    print CONTROL "\[" . $begin . "," . $end . "\], ";
}


$begin = $end+1;
$end += $composed_task_train_episodes_count;

foreach $i (1..($atomic_task_count**2+$atomic_task_count**3)) {
    print COMP "\[" . $begin . "," . $end . "\], ";
    print CONTROL "\[" . $begin . "," . $end . "\], ";
}

$begin = $end+1;
$end += $composed_task_test_episodes_count;

foreach $i (1..($atomic_task_count**2+$atomic_task_count**3-1)) {
    print COMP "\[" . $begin . "," . $end . "\], ";
    print CONTROL "\[" . $begin . "," . $end . "\], ";
}
print COMP "\[" . $begin . "," . $end . "\]\]\n";
print CONTROL "\[" . $begin . "," . $end . "\]\]\n";

$bottom = << 'END_BOTTOM';
     }
  }
}
END_BOTTOM
print COMP $bottom;
print CONTROL $bottom;

close COMP;
close CONTROL;
