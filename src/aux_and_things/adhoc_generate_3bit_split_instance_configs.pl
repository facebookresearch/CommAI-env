#!/usr/bin/perl -w

$name_string = shift;

$composition_type = shift;

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


@combinations = ();

$i=1;
while ($i<=$atomic_task_count) {
    $task_specification = << "END_TASK_SPECIFICATION";
    "LookupTaskR3D$i": {
      "type": "tasks.micro.$lookup_table_name.LookupTaskR3D$i"
    },
END_TASK_SPECIFICATION

    print COMP $task_specification;
    print CONTROL $task_specification;

    $control_i = $i + $atomic_task_count;
    $j=1;
    while ($j<=$atomic_task_count) {
        $control_j = $j + $atomic_task_count;
        $composed_task_specification = << "END_TASK_SPECIFICATION";
    "${composition_type}LookupTaskR3D${i}_${j}": {
      "type": "tasks.micro.$lookup_table_name.FuncLookupTaskR3D${i}_${j}"
    },
    "${composition_type}LookupTaskR3D${control_i}_${control_j}": {
      "type": "tasks.micro.$lookup_table_name.FuncLookupTaskR3D${control_i}_${control_j}"
    },
    "${composition_type}LookupTestTaskR3D${i}_${j}": {
      "type": "tasks.micro.$lookup_table_name.FuncLookupTestTaskR3D${i}_${j}"
    },
    "${composition_type}LookupTestTaskR3D${control_i}_${control_j}": {
      "type": "tasks.micro.$lookup_table_name.FuncLookupTestTaskR3D${control_i}_${control_j}"
    },
END_TASK_SPECIFICATION
        if ($i==$atomic_task_count && $j==$atomic_task_count) {
            $composed_task_specification =~ s/,$//;
        }
        print COMP $composed_task_specification;
        print CONTROL $composed_task_specification;
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
print CONTROL $connector;

foreach $i (1..$atomic_task_count) {
    print COMP "\"LookupTaskR3D$i\", ";
    print CONTROL "\"LookupTaskR3D$i\", ";
}

@composed_names = ();
foreach $i_j (@combinations) {
    $composed_name = "\"" . $composition_type . "LookupTaskR3D" . $i_j . "\"";
    push @composed_names,$composed_name;
}
print COMP join ", ", @composed_names;
print CONTROL join ", ", @composed_names;

print COMP ", ";
print CONTROL ", ";


@composed_test_names = ();
@control_test_names = ();
foreach $i_j (@combinations) {
    $composed_test_name =  "\"" . $composition_type . "LookupTestTaskR3D" . $i_j . "\"";
    ($i,$j) = split "_",$i_j;
    push @composed_test_names,$composed_test_name;
    $control_test_name = "\"" . $composition_type . "LookupTestTaskR3D" . ($i+$atomic_task_count) . "_" .
        ($j+$atomic_task_count) . "\"";
    push @control_test_names,$control_test_name;
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

foreach $i (1..($atomic_task_count**2)) {
    print COMP "\[" . $begin . "," . $end . "\], ";
    print CONTROL "\[" . $begin . "," . $end . "\], ";
}

$begin = $end+1;
$end += $composed_task_test_episodes_count;

foreach $i (1..($atomic_task_count**2-1)) {
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
