# GitHub Action That Retrieves Model Runs From Weights & Biases

## Motivation: Facilitating ML-Ops

The code-review and deployment process re: Machine Learning often involves making decisions about merging or deploying code where critical information regarding model performance and statistics is not readily available.  This is due to the friction in including logging and statistics from model training runs tracking in Pull Requests.  For example, consider this excerpt from a [real pull-request](https://github.com/kubeflow/code-intelligence/pull/54):

>![](/images/pr.png)

In an ideal world, the participants in the above code review should have all the information to them available in the context of pull request that they need to evaluate the changes to the code, including:

- Model performance metrics and statistics
- Comparison with baselines and the current model in production on a holdout dataset
- Verification that the metrics and statistics correspond to the code changed in the PR, potentially by tying the results to a commit SHA.
- Data versioning
- etc.

This GitHub Action provides tools that facilitate the inclusion of model training results with comparisons of other runs (for example baseline models or current best models), by pulling information regarding your model runs you log in [Weights & Biases](https://www.wandb.com/) (W&B) into a **pull request automatically**.  W&B is an experiment tracking system for machine learning models, and is free for open source projects. See these [docs](https://docs.wandb.com/) for more information regarding the various apis and integrations available for W&B.

## Features of This Action

This action fetches all model runs that either:

1. **Correspond to a git commit SHA**, for example the commit SHA that triggered the Action.  See the documenation for the buit-in environment variable [GITHUB_SHA](https://help.github.com/en/articles/virtual-environments-for-github-actions#environment-variables)
2. **Contain at least one tag out of a list of tags that you specify.**  This might be used to obtain a set of baseline run(s) to compare the runs for the current SHA.

TODO ... 