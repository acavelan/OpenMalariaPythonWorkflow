#!/bin/bash

#SBATCH --job-name=@jobname@
#SBATCH --time=00:30:00
#SBATCH --account=@account@
#SBATCH --qos=30min
#SBATCH --output=log/%a.err #/dev/null
#SBATCH --error=log/%a.out #/dev/null
#SBATCH --mem=1G
#SBATCH --array=1-@N@%1000

export LMOD_DISABLE_SAME_NAME_AUTOSWAP=no

ml OpenMalaria/45.0-iomkl-2019.01

SEEDFILE="commands.txt"
SEED=$(sed -n ${SLURM_ARRAY_TASK_ID}p $SEEDFILE)
eval $SEED
