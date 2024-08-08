#!/usr/bin/env bash

#SBATCH --partition=mypartition
#SBATCH -N 1
#SBATCH --job-name=test
#SBATCH --output=/tmp/%j.out
#SBATCH --error=/tmp/%j.err
#SBATCH --licenses=test_product.test_feature@flexlm:42

srun /tmp/application.py
