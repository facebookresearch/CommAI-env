#!/usr/bin/perl -w

use List::Util qw(shuffle);

$name_string = shift;

$composition_type = shift;

$lookup_table_name = shift;

$atomic_task_count = shift;

$train_composed_task_count = shift;

$atomic_task_training_episodes_count = shift;

$composed_task_training_episodes_count = shift;

$composed_task_test_episodes_count = shift;

@combinations = ();

$comp_file = "tasks_config." . $name_string . "_compositional.json";
$mixed_control_file = "tasks_config." . $name_string . "_mixed_control.json";
$pure_control_file = "tasks_config." . $name_string . "_pure_control.json";

`rm -f $comp_file`;
`rm -f $mixed_control_file`;
`rm -f $pure_control_file`;

open COMP,">$comp_file";
open MIXED_CONTROL,">$mixed_control_file";
open PURE_CONTROL,">$pure_control_file";

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
print MIXED_CONTROL $preamble;
print PURE_CONTROL $preamble;

$i=1;
while ($i<=$atomic_task_count) {
    $task_specification = << "END_TASK_SPECIFICATION";
    "LookupTaskR2D$i": {
      "type": "tasks.micro.$lookup_table_name.LookupTaskR2D$i"
    },
END_TASK_SPECIFICATION

    print COMP $task_specification;
    print MIXED_CONTROL $task_specification;
    print PURE_CONTROL $task_specification;

    $j=1;
    while ($j<=$atomic_task_count) {
        $compositional_task_specification = << "END_TASK_SPECIFICATION";
    "${composition_type}LookupTaskR2D${i}_${j}": {
      "type": "tasks.micro.$lookup_table_name.FuncLookupTaskR2D${i}_${j}"
    },
END_TASK_SPECIFICATION
        print COMP $compositional_task_specification;
        print MIXED_CONTROL $compositional_task_specification;
        print PURE_CONTROL $compositional_task_specification;
        $control_i = $i+$atomic_task_count;
        $control_j = $j+$atomic_task_count;
        $control_task_specification = << "END_TASK_SPECIFICATION";
    "${composition_type}LookupTaskR2D${control_i}_${control_j}": {
      "type": "tasks.micro.$lookup_table_name.FuncLookupTaskR2D${control_i}_${control_j}"
    },
END_TASK_SPECIFICATION
        if ($i==$atomic_task_count && $j==$atomic_task_count) {
            $control_task_specification =~ s/,$//;
        }
        print COMP $control_task_specification;
        print MIXED_CONTROL $control_task_specification;
        print PURE_CONTROL $control_task_specification;

        push @combinations, $i . "_" . $j;

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
print MIXED_CONTROL $connector;
print PURE_CONTROL $connector;

foreach $i (1..$atomic_task_count) {
    print COMP "\"LookupTaskR2D$i\", ";
    print MIXED_CONTROL "\"LookupTaskR2D$i\", ";
    print PURE_CONTROL "\"LookupTaskR2D$i\", ";
}

@shuffled = shuffle @combinations;

$t = 0;
while ($t<=$#shuffled) {
    $i_j = $shuffled[$t];
    ($i,$j) = split "_",$i_j;

    $compositional_composed_name =  "\"" . $composition_type . "LookupTaskR2D" . $i_j . "\"";
    $control_composed_name =
        "\"" . $composition_type . "LookupTaskR2D" . ($i+$atomic_task_count) . "_" . ($j+$atomic_task_count) . "\"";

    push @compositional_composed_names, $compositional_composed_name;
    push @pure_control_composed_names, $control_composed_name;

    if ($t<$train_composed_task_count) {
        push @mixed_control_composed_names,$compositional_composed_name;
    }
    else {
        push @mixed_control_composed_names,$control_composed_name;
    }

    $t++;
}

print COMP join ", ",@compositional_composed_names;
print MIXED_CONTROL join ", ",@mixed_control_composed_names;
print PURE_CONTROL join ", ",@pure_control_composed_names;


print COMP "\],\n         \"intervals\": \[";
print MIXED_CONTROL "\],\n         \"intervals\": \[";
print PURE_CONTROL "\],\n         \"intervals\": \[";

foreach $i (1..$atomic_task_count) {
    $begin = $atomic_task_training_episodes_count * ($i-1);
    $end = ($atomic_task_training_episodes_count * $i) -1 ;
    print COMP "\[" . $begin . "," . $end . "\], ";
    print MIXED_CONTROL "\[" . $begin . "," . $end . "\], ";
    print PURE_CONTROL "\[" . $begin . "," . $end . "\], ";
}

$begin = $end+1;
$end += $composed_task_training_episodes_count;

foreach $i (1..$train_composed_task_count) {
    print COMP "\[" . $begin . "," . $end . "\], ";
    print MIXED_CONTROL "\[" . $begin . "," . $end . "\], ";
    print PURE_CONTROL "\[" . $begin . "," . $end . "\], ";
}

$test_composed_task_count = $atomic_task_count**2-$train_composed_task_count;

$begin = $end+1;
$end += $composed_task_test_episodes_count;

foreach $i (1..($test_composed_task_count-1)) {
    print COMP "\[" . $begin . "," . $end . "\], ";
    print MIXED_CONTROL "\[" . $begin . "," . $end . "\], ";
    print PURE_CONTROL "\[" . $begin . "," . $end . "\], ";
}
print COMP "\[" . $begin . "," . $end . "\]\]\n";
print MIXED_CONTROL "\[" . $begin . "," . $end . "\]\]\n";
print PURE_CONTROL "\[" . $begin . "," . $end . "\]\]\n";

$bottom = << 'END_BOTTOM';
     }
  }
}
END_BOTTOM
print COMP $bottom;
print MIXED_CONTROL $bottom;
print PURE_CONTROL $bottom;

close COMP;
close MIXED_CONTROL;
close PURE_CONTROL;
