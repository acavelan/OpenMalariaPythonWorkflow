#!/bin/bash

#SBATCH --job-name=@jobname@
#SBATCH --time=00:30:00
#SBATCH --account=@account@
#SBATCH --qos=30min
#SBATCH --output=%a.err #%A_%a.err
#SBATCH --error=%a.err #%A_%a.out
#SBATCH --mem=1G
#SBATCH --array=1-@N@%400

export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK

export LMOD_DISABLE_SAME_NAME_AUTOSWAP=no

ml iomkl/2019.01
ml CMake/3.13.3-GCCcore-8.2.0
ml GSL/2.5-iomkl-2019.01
ml XSD/4.0.0-GCCcore-8.2.0

SEEDFILE="commands.txt"
SEED=$(sed -n ${SLURM_ARRAY_TASK_ID}p $SEEDFILE)
eval $SEED
