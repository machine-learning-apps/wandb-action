![Actions Status](https://github.com/machine-learning-apps/wandb-action/workflows/Tests/badge.svg)


# GitHub Action That Retrieves Model Runs From Weights & Biases

Weights & Biases [homepage](https://www.wandb.com/)

<!-- TOC depthFrom:1 depthTo:6 withLinks:1 updateOnSave:1 orderedList:0 -->

- [Motivation: Facilitating ML-Ops](#motivation-facilitating-ml-ops)
- [Features of This Action](#features-of-this-action)
    - [Querying Model Runs](#querying-model-runs)
    - [Querying Additonal Baseline Runs](#querying-additonal-baseline-runs)
    - [Saving & Displaying Model Run Data](#saving-displaying-model-run-data)
- [Usage](#usage)
    - [Inputs](#inputs)
        - [Mandatory Inputs](#mandatory-inputs)
        - [Optional Inputs](#optional-inputs)
    - [Outputs](#outputs)

<!-- /TOC -->

## Motivation: Facilitating ML-Ops

The code-review and deployment process re: Machine Learning often involves making decisions about merging or deploying code where critical information regarding model performance and statistics are not readily available.  This is due to the friction in including logging and statistics from model training runs in Pull Requests.  For example, consider this excerpt from a [real pull-request](https://github.com/kubeflow/code-intelligence/pull/54) concerning a machine learning project:

>![](/images/pr.png)

In an ideal world, the participants in the above code review should be provided with all of the context necessary to evaluate the PR, including:

- Model performance metrics and statistics
- Comparison with baselines and other models on a holdout dataset
- Verification that the metrics and statistics correspond to the code changed in the PR, by tying the results to a commit SHA.
- Data versioning
- etc.

This GitHub Action provides tools that facilitate the inclusion of model training results with comparisons of other runs (for example baseline models or current best models), by pulling information regarding model runs you log in [Weights & Biases](https://www.wandb.com/) (W&B) into a **pull request automatically**.  W&B is an experiment tracking system for machine learning models, and is free for open source projects. See these [docs](https://docs.wandb.com/) for more information about the W&B api.

When composed with [other Actions](https://github.com/machine-learning-apps/actions-ml-cicd), this Action is designed to enable [CI/CD for machine learning](https://blog.paperspace.com/ci-cd-for-machine-learning-ai/).

## Features of This Action

### Querying Model Runs

This action fetches all model runs that either:

1. **Correspond to a git commit SHA**, for example the commit SHA that triggered the Action.  See the documenation for the buit-in environment variable [GITHUB_SHA](https://help.github.com/en/articles/virtual-environments-for-github-actions#environment-variables). Typical use cases for querying model runs with a git commit SHA:
    - There are many experiments generated from the same code, such has hyper-parameter tuning.
    - You want to automatically fetch experiment results that correspond to the commit SHA that triggered the GitHub Action.  This can help ensure that your experiment results are not stale relative to your code.

      Querying by git commit SHA **assumes you have logged a config variable named `github_sha`** to your [config variables](https://docs.wandb.com/wandb/config).  Example:
    
        ```py
        import wandb, os
        # You set the environment variable before running this script programatically with the SHA
        github_sha = os.getenv('GITHUB_SHA')
        wandb.config.github_sha = github_sha
        ```

        In addition to querying by commit SHA, you can apply **an additional filter for a secondary SHA**. You might use this filter in addition to the commit SHA when you other external variables to the code such as data version that you want to track.  For example, you can version your data with [Pachyderm](https://www.pachyderm.io), which gives you a SHA corresponding to you data version.  Similar to the github SHA, **supplying an argument for secondary SHA assumes you have logged a config variable named `secondary_sha`** to your experiment in W&B.

2. **Match a run id**:  The run id corresponds to the unique identifier found in the URL when viewing the run on W&B: `https://app.wandb.ai/{entity_name}/{project_name}/runs/{run_id}`.

### Querying Additonal Baseline Runs

It is often useful to compare model runs against baseline runs or your current best models in order to properly assess model performance.  Therefore, in addition to the runs described above, you can also query runs by tag, which is a label you can assign either programatically or in the W&B user interface.  You can supply a list of tags as additional runs that will be queried.  See the `BASELINE_TAGS` input in the [Inputs](#inputs) section below).  Two properties of baseline runs that are important:

- Baseline runs will be marked as `baseline` in the output csv file in a column named `__eval.category`.  See the [outputs](#outputs) section for more detail.
- Baselines runs are mutually exclusive with other runs that you are querying.  If there are runs that are in both the baseline set and the candidate set, this will be resolved by moving those runs into the candidate set. The candidate set refers to any runs returned by methods 1 or 2 in Querying Model Runs.

### Saving & Displaying Model Run Data

**This Action saves a csv file called `wandb_report.csv` into the path specified by the [default environment variable](https://help.github.com/en/articles/virtual-environments-for-github-actions#environment-variables) `GITHUB_WORKSPACE` set for you in GitHub Actions**,  which allows this data to be accessed by subsequent Actions.  Information in this CSV can be displayed in a variety of ways, such as a markdown formatted comment in a pull request or via the [GitHub Checks](https://developer.github.com/v3/checks/) API.

This csv file always has the following fields:
- `run.url`: the url for the run in the W&B api.
- `run.name`: the name of the run. This is automatically set by wandb if not specified by the user.
- `run.tags`: a list with all of the tags assigned to the run.
- `run.id`: the id associated with the run.  This corresponds to the input `RUN_ID`
- `run.entity`: this name of the entity that contains the project the run can be found in.  This is similar to an org in GitHub.
- `run.project`: the name of the project that contains the run.  This is simlar to a repo in GitHub.
- `github_sha`: the config variable `github_sha`.
- `__eval.category`: this field will contain either the value `candiate` or `baseline`, depending on how the run was queried.

In addition to the above fields the user can specify the following additional fields from model runs.  See the [Inputs](#inputs) section for more information on how to supply these inputs.

- [summary_metrics](https://docs.wandb.com/wandb/log#summary-metrics): you can specify a list of summary metrics, for example:  `"['acc', 'loss', 'val_acc', 'val_loss']"`

- [config variables](https://docs.wandb.com/wandb/config): specify a list of configuraiton variables, for example: `"['learning_rate', 'num_layers']"`.  These fields will be prepended with an underscore in the output csv file.

Below is an example of the contents of the csv file:

| run.url                                                        | run.name       | run.tags             | run.id   | run.entity | run.project          | github_sha |    acc |   loss | val_acc | val_loss | _docker_digest | __eval.category |
| -------------------------------------------------------------- | -------------- | -------------------- | -------- | ---------- | -------------------- | ---------- | ------ | ------ | ------- | -------- | -------------- | --------------- |
| https://app.wandb.ai/github/predict-issue-labels/runs/e6lo523p | dashing-leaf-4 | []                   | e6lo523p | github     | predict-issue-labels | 86edd034aaba1498dbae6465cf994de90be6a4b2       | 0.896… | 0.540… |   1.000 |   1.054… |                | candidate       |
| https://app.wandb.ai/github/predict-issue-labels/runs/15u8cbod | happy-frog-3   | ['baseline', 'test'] | 15u8cbod | github     | predict-issue-labels | 86edd034aaba1498dbae6465cf994de90be6a4b2       | 0.881… | 0.605… |   0.500 |   1.080… |                | candidate       |
| https://app.wandb.ai/github/predict-issue-labels/runs/cqigzoxc | dandy-river-1  | ['baseline']         | cqigzoxc | github     | predict-issue-labels | 86edd034aaba1498dbae6465cf994de90be6a4b2           | 0.925… | 0.441… |   0.375 |   1.095… |                | baseline        |


## Usage

### Inputs

#### Mandatory Inputs
  1. `WANDB_API_KEY`: your W&B api key.
  2. `PROJECT_NAME`:  The entity/project name associated with your wandb project.  Example - 'github/predict-issue-labels'
  3. Either `RUN_ID` or `FILTER_GITHUB_SHA` must be specified, even though these are both optional inputs.  See below for more details:


#### Optional Inputs

  1. `RUN_ID`: the run id, which can be found in the url https://app.wandb.ai/{entity_name}/{project_name}/runs/{run_ID}.  When supplying this input, `FILTER_GITHUB_SHA` and `FILTER_SECONDARY_SHA` are ignored and only the run corresponding to this id (along with any baselines corresponding to the input BASELINE_TAGS) are returned.
  2. `FILTER_GITHUB_SHA`: The git SHA that you want to filter runs by.  This assumes you have a logged a configuration variable named 'github_sha' to your runs. A common usage pattern is to supply the built-in environment variable $GITHUB_SHA, to get the commit SHA that triggered the workflow.  Note that this argument is ignored if `RUN_ID` is specified.
  3. `FILTER_SECONDARY_SHA`: This is an optional field you can filter your runs by.  This assumes you have logged a configuration variable named 'secondary_sha' to your model runs.  You might use this field for data versioning.  Note that this argument is ignored if `RUN_ID` is specified.
  4. `BASELINE_TAGS`:  A list of tags that correspond to runs you want to retrieve in addition to those that correspond to the FILTER_GITHUB_SHA.  You would typically use this field to obtain baseline runs to compare your current runs against.  Example - `"['baseline']"`
  5. `DISPLAY_METRICS`:  A list of summary metrics you want to retain for the csv file that is written to the actions environment.  Example - `"['acc', 'loss', 'val_acc', 'val_loss']"`
  6. `DISPLAY_CONFIG_VARS`: A list of configuration variables you want to retain for the csv file written to the actions environment.  Example - `"['learning_rate', 'num_layers']"`
  7. `DEBUG`: Setting this variable to any value will turn debug mode on.

### Outputs

You can reference the outputs of an action using [expression syntax](https://help.github.com/en/articles/contexts-and-expression-syntax-for-github-actions).

1. `BOOL_COMPLETE`: True if there is at least 1 finished run and no runs that have a state of 'running' else False
2. `BOOL_SINGLE_RUN`: True if there is only 1 run returned from the query else False
3. `NUM_FINISHED`: The number of non-baseline runs with a state of 'finished'
4. `NUM_RUNNING`: The number of non-baseline runs with a state of 'running'
5. `NUM_CRASHED`: The number of non-baseline runs with a state of 'crashed'
6. `NUM_ABORTED`: The number of non-baseline runs with a state of 'aborted'
7. `NUM_BASELINES`: The number of baseline runs returned.  See [this section](#querying-additonal-baseline-runs) for more context regarding baseline runs.

## Keywords
 MLOps, Machine Learning, Data Science
