<center>

# Currency Rate Finder - With Google Play Store

[![python](https://img.shields.io/badge/-Python_3.8_%7C_3.9_%7C_3.10%7C_3.11-blue?logo=python&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![pytorch](https://img.shields.io/badge/PyTorch_2.0+-ee4c2c?logo=pytorch&logoColor=white)](https://pytorch.org/get-started/locally/)
[![lightning](https://img.shields.io/badge/-Lightning_2.0+-792ee5?logo=pytorchlightning&logoColor=white)](https://pytorchlightning.ai/)
[![hydra](https://img.shields.io/badge/Config-Hydra_1.3-89b8cd)](https://hydra.cc/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![tests](https://github.com/Mai0313/ingame-price-finder/actions/workflows/test.yml/badge.svg)](https://github.com/Mai0313/ingame-price-finder/actions/workflows/test.yml)
[![code-quality](https://github.com/Mai0313/ingame-price-finder/actions/workflows/code-quality-check.yml/badge.svg)](https://github.com/Mai0313/ingame-price-finder/actions/workflows/code-quality-check.yml)
[![codecov](https://codecov.io/gh/Mai0313/ingame-price-finder/branch/master/graph/badge.svg)](https://codecov.io/gh/Mai0313/ingame-price-finder)
[![license](https://img.shields.io/badge/License-MIT-green.svg?labelColor=gray)](https://github.com/Mai0313/ingame-price-finder/tree/master?tab=License-1-ov-file)
[![PRs](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/Mai0313/ingame-price-finder/pulls)
[![contributors](https://img.shields.io/github/contributors/Mai0313/ingame-price-finder.svg)](https://github.com/Mai0313/ingame-price-finder/graphs/contributors)

</center>

## Description

### It will present you where the cheapest rate country for google play is!

## Installation

#### Pip

```bash
# clone project
git clone https://github.com/YourGithubName/your-repo-name
cd your-repo-name

# [OPTIONAL] create conda environment
conda create -n myenv python=3.9
conda activate myenv

# install pytorch according to instructions
# https://pytorch.org/get-started/

# install requirements
pip install -r requirements.txt
```

#### Conda

```bash
# clone project
git clone https://github.com/YourGithubName/your-repo-name
cd your-repo-name

# create conda environment and install dependencies
conda env create -f environment.yaml -n myenv

# activate conda environment
conda activate myenv
```

## How to run

Train model with default configuration

```bash
# train on CPU
python src/train.py trainer=cpu

# train on GPU
python src/train.py trainer=gpu
```

Train model with chosen experiment configuration from [configs/experiment/](configs/experiment/)

```bash
python src/train.py experiment=experiment_name.yaml
```

You can override any parameter from command line like this

```bash
python src/train.py trainer.max_epochs=20 data.batch_size=64
```
