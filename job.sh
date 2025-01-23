#!/bin/bash

#SBATCH --job-name=@jobname@
#SBATCH --time=00:30:00
#SBATCH --account=@account@
#SBATCH --qos=@qos@
#SBATCH --output=log/%A_%a.out  # Job array output
#SBATCH --error=log/%A_%a.err   # Job array error
#SBATCH --mem=1G
#SBATCH --cpus-per-task=@CPUS_PER_TASK@  # Number of CPUs per job
#SBATCH --array=1-@N@            # Adjust @M@ to the number of job bundles

export LMOD_DISABLE_SAME_NAME_AUTOSWAP="no"

# Load GNU parallel
ml parallel

# Prepare environment
@prepare@

# Define the seed file
SEEDFILE="commands.txt"

# Calculate the start and end line numbers for this job array task
START=$(( (SLURM_ARRAY_TASK_ID - 1) * @BATCH_SIZE@ + 1 ))
END=$(( SLURM_ARRAY_TASK_ID * @BATCH_SIZE@ ))

# Pipe the relevant lines to GNU parallel
sed -n "${START},${END}p" "$SEEDFILE" | parallel -j"@CPUS_PER_TASK@"
