#!/usr/bin/perl -w

$name_string = shift;
$num_bits = shift;
$composition_type = shift;
$lookup_table_name = shift;
$atomic_task_count = shift;
$atomic_task_episodes_count = shift;
$composed_task_train_episodes_count = shift;
$composed_task_test_episodes_count = shift;
# Configuration file type: TRAIN_SEPARATE or ALL_TOGETHER
$config_type = shift;

# Output file names for the compositional and control setups
$comp_file = $name_string . "_compositional.json";
$control_file = $name_string . "_control.json";

`rm -f $comp_file`;
`rm -f $control_file`;

open COMP,">$comp_file";
open CONTROL,">$control_file";

if ($config_type eq "TRAIN_SEPARATE") {
 $train_file = $name_string . "_train.json";
 `rm -f $train_file`;
 open TRAIN,">$train_file";
}

# 1. PRINT THE PREAMBLE
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

if ($config_type eq "TRAIN_SEPARATE") {
  print TRAIN $preamble;
}
print COMP $preamble;
print CONTROL $preamble;

# 2. PRINT THE SUPERSET OF TASKS USED IN THIS CONFIG
@combinations = ();

$i=1;
while ($i<=$atomic_task_count) {
    $task_specification = << "END_TASK_SPECIFICATION";
    "LookupTaskR${num_bits}D$i": {
      "type": "tasks.micro.$lookup_table_name.LookupTaskR${num_bits}D$i"
    },
END_TASK_SPECIFICATION
    if ($config_type eq "TRAIN_SEPARATE") {
      print TRAIN $task_specification;
    }
    print COMP $task_specification;
    print CONTROL $task_specification;

    $control_i = $i + $atomic_task_count;
    $j=1;
    while ($j<=$atomic_task_count) {
        $control_j = $j + $atomic_task_count;
        $composed_task_specification = << "END_TASK_SPECIFICATION";
    "${composition_type}LookupTaskR${num_bits}D${i}_${j}": {
      "type": "tasks.micro.$lookup_table_name.${composition_type}LookupTaskR${num_bits}D${i}_${j}"
    },
    "${composition_type}LookupTaskR${num_bits}D${control_i}_${control_j}": {
      "type": "tasks.micro.$lookup_table_name.${composition_type}LookupTaskR${num_bits}D${control_i}_${control_j}"
    },
    "${composition_type}LookupTestTaskR${num_bits}D${i}_${j}": {
      "type": "tasks.micro.$lookup_table_name.${composition_type}LookupTestTaskR${num_bits}D${i}_${j}"
    },
    "${composition_type}LookupTestTaskR${num_bits}D${control_i}_${control_j}": {
      "type": "tasks.micro.$lookup_table_name.${composition_type}LookupTestTaskR${num_bits}D${control_i}_${control_j}"
    },
END_TASK_SPECIFICATION
        if ($i==$atomic_task_count && $j==$atomic_task_count) {
            $composed_task_specification =~ s/,$//;
        }
        if ($config_type eq "TRAIN_SEPARATE") {
          print TRAIN $composed_task_specification;
        }
        print COMP $composed_task_specification;
        print CONTROL $composed_task_specification;
        push @combinations, $i . "_" . $j;
        $j++;
    }
    $i++;
}

# 3. PRINT THE SCHEDULER
$connector = << 'CONNECTOR';
  },
  "scheduler":
  {
     "type": "core.scheduler.IntervalTaskScheduler",
     "args": {
         "tasks": [
CONNECTOR
chomp $connector;
if ($config_type eq "TRAIN_SEPARATE") {
  print TRAIN $connector;
}
print COMP $connector;
print CONTROL $connector;

# 3.1 Print tasks
if ($atomic_task_episodes_count > 0) {
  @atomic_names = ();
  foreach $i (1..$atomic_task_count) {
    $atomic_name = "\"LookupTaskR${num_bits}D$i\"";
    push @atomic_names, $atomic_name;
  }
  if ($config_type eq "TRAIN_SEPARATE") {
    print TRAIN join ", ", @atomic_names;
  } else {
    print COMP join ", ", @atomic_names;
    print CONTROL join ", ", @atomic_names;
  }
}

if ($composed_task_train_episodes_count > 0) {
  if ($atomic_task_episodes_count > 0) {
    if ($config_type eq "TRAIN_SEPARATE") {
      print TRAIN ", ";
    } else {
      print COMP ", ";
      print CONTROL ", ";
    }
  }
  @composed_names = ();
  foreach $i_j (@combinations) {
      $composed_name = "\"" . $composition_type . "LookupTaskR${num_bits}D"
        . $i_j . "\"";
      push @composed_names,$composed_name;
  }
  if ($config_type eq "TRAIN_SEPARATE") {
    print TRAIN join ", ", @composed_names;
  } else {
    print COMP join ", ", @composed_names;
    print CONTROL join ", ", @composed_names;
  }
}

if ($composed_task_test_episodes_count > 0) {
  if (($composed_task_train_episodes_count > 0 ||
    $atomic_task_episodes_count > 0) && $config_type ne "TRAIN_SEPARATE") {
    print COMP ", ";
    print CONTROL ", ";
  }
  @composed_test_names = ();
  @control_test_names = ();
  foreach $i_j (@combinations) {
      $composed_test_name =  "\"" . $composition_type
        . "LookupTestTaskR${num_bits}D" . $i_j . "\"";
      ($i,$j) = split "_",$i_j;
      push @composed_test_names,$composed_test_name;
      $control_test_name = "\"" . $composition_type
        . "LookupTestTaskR${num_bits}D" . ($i+$atomic_task_count)
        . "_" . ($j+$atomic_task_count) . "\"";
      push @control_test_names,$control_test_name;
  }
  print COMP join ", ", @composed_test_names;
  print CONTROL join ", ", @control_test_names;
}

if ($config_type eq "TRAIN_SEPARATE") {
  print TRAIN "\],\n";
}
print COMP "\],\n";
print CONTROL "\],\n";

# 3.2 Print intervals
if ($config_type eq "TRAIN_SEPARATE") {
  print TRAIN "         \"intervals\": \[";
}
print COMP "         \"intervals\": \[";
print CONTROL "         \"intervals\": \[";


if ($atomic_task_episodes_count > 0) {
  $begin = 0;
  $end = $atomic_task_episodes_count-1;

  foreach $i (1..$atomic_task_count) {
      if ($config_type eq "TRAIN_SEPARATE") {
        print TRAIN "\[" . $begin . "," . $end . "\]";
      } else {
        print COMP "\[" . $begin . "," . $end . "\]";
        print CONTROL "\[" . $begin . "," . $end . "\]";
      }
      if ($i < $atomic_task_count) {
        if ($config_type eq "TRAIN_SEPARATE") {
          print TRAIN ", ";
        } else {
          print COMP ", ";
          print CONTROL ", ";
        }
      }
  }
}

if ($composed_task_train_episodes_count > 0) {
  if ($atomic_task_episodes_count > 0) {
    if ($config_type eq "TRAIN_SEPARATE") {
      print TRAIN ", ";
    } else {
      print COMP ", ";
      print CONTROL ", ";
    }
  }

  $begin = $atomic_task_episodes_count;
  $end = $begin + $composed_task_train_episodes_count - 1;

  foreach $i (1..($atomic_task_count**2)) {
    if ($config_type eq "TRAIN_SEPARATE") {
      print TRAIN "\[" . $begin . "," . $end . "\]";
      if ($i < $atomic_task_count**2) {
        print TRAIN ", ";
      }
    } else {
      print COMP "\[" . $begin . "," . $end . "\]";
      print CONTROL "\[" . $begin . "," . $end . "\]";
      if ($i < $atomic_task_count**2) {
        print COMP ", ";
        print CONTROL ", ";
      }
    }
  }
}

if ($composed_task_test_episodes_count > 0) {
  if ($config_type eq "TRAIN_SEPARATE") {
    $begin = 0;
  } else {
    $begin = $atomic_task_episodes_count + $composed_task_train_episodes_count;
  }
  $end = $begin + $composed_task_test_episodes_count - 1;

  if (($atomic_task_episodes_count > 0 ||
    $composed_task_train_episodes_count > 0) &&
    $config_type ne "TRAIN_SEPARATE") {
      print COMP ", ";
      print CONTROL ", ";
  }

  foreach $i (1..($atomic_task_count**2-1)) {
      print COMP "\[" . $begin . "," . $end . "\], ";
      print CONTROL "\[" . $begin . "," . $end . "\], ";
  }
  print COMP "\[" . $begin . "," . $end . "\]";
  print CONTROL "\[" . $begin . "," . $end . "\]";
}

if ($config_type eq "TRAIN_SEPARATE") {
  print TRAIN "\]\n";
}
print COMP "\]\n";
print CONTROL "\]\n";

# 4. CLOSE OFF THE TASK CONFIG FILE
$bottom = << 'END_BOTTOM';
     }
  }
}
END_BOTTOM
if ($config_type eq "TRAIN_SEPARATE") {
  print TRAIN $bottom;
}
print COMP $bottom;
print CONTROL $bottom;

if ($config_type eq "TRAIN_SEPARATE") {
  close TRAIN;
}
close COMP;
close CONTROL;
