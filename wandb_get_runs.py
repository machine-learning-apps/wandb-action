"""
Retrieves all runs from wandb that either:
- correspond to a Git SHA
- have specific tags.

The purpose is to compare runs from a given SHA to runs you may have tagged as baselines.
"""


import os
import wandb
import logging
import pandas as pd

logging.root.setLevel(logging.DEBUG)

api = wandb.Api()

# Read Inputs
project_name = os.getenv('INPUT_PROJECT_NAME')
save_folder = os.getenv('GITHUB_WORKSPACE')
metrics = eval(os.getenv('INPUT_DISPLAY_METRICS'))
config_vars = eval(os.getenv('INPUT_DISPLAY_CONFIG_VARS'))
debug = True if os.getenv('INPUT_DEBUG') else False

# Read Query Parameters
secondary_sha = os.getenv('INPUT_FILTER_SECONDARY_SHA')
github_sha = os.getenv('INPUT_FILTER_GITHUB_SHA')
tags = eval(os.getenv('INPUT_BASELINE_TAGS'))

print(f'Debug Mode On: {debug}')

if debug:
    logging.debug(f'INPUT_BASELINE_TAGS: {tags}')
    logging.debug(f'INPUT_FILTER_GITHUB_SHA: {github_sha}')
    logging.debug(f'INPUT_FILTER_SECONDARY_SHA: {secondary_sha}')
    logging.debug(f'INPUT_DISPLAY_CONFIG_VARS: {config_vars}')
    logging.debug(f'INPUT_DISPLAY_METRICS: {metrics}')

#validate input
def check_list(var, name):
    assert isinstance(var, list), f"{name} argument must evaluate to a python list"
    if var:
        assert max([isinstance(x, str) for x in var]), f"{name} argument must be a list of strings"

check_list(tags, "BASELINE_TAGS")
check_list(metrics, "METRICS")
check_list(config_vars, "CONFIG_VARS")


#run a query for all runs matching the github sha AND optionally the secondary sha
if secondary_sha:
    runs = api.runs(project_name, {"$and": [{"config.github_sha": f"{github_sha}"},
                                            {"config.secondary_sha": f"{secondary_sha}"}]
                                  }
                   )
    # baseline runs should be mutually exclusive from the experimental runs
    # the only time the github_sha is allowed to not exist is for baseline runs             
    baseline_runs=api.runs(project_name, {"$and": [{"tags": {"$in": tags}},
                                                   {"$or": [{"config.github_sha": { "$ne": f"{github_sha}"}},
                                                            {"config.github_sha": { "$exists": False}},
                                                            {"config.secondary_sha": { "$ne": f"{secondary_sha}"}},
                                                            {"config.secondary_sha": { "$exists": False}}]
                                                   }]
                                         }
                           )

else:
    runs = api.runs(project_name, {"config.github_sha": f"{github_sha}"})
    # baseline runs should be mutually exclusive from the experimental runs 
    # the only time the github_sha is allowed to not exist is for baseline runs
    baseline_runs = api.runs(project_name, {"$and": [{"tags": {"$in": tags}},
                                                            { "$or": [{"config.github_sha": { "$ne": f"{github_sha}"}},
                                                                      {"config.github_sha": { "$exists": False}}]
                                                            },
                                                    ]
                                            }
                            )

runs = list(runs)
baseline_runs = list(baseline_runs)

finished_runs = [run for run in runs if runs and run.state == 'finished']
running_runs = [run for run in runs if runs and run.state == 'running']
crashed_runs = [run for run in runs if run.state == 'crashed']
aborted_runs = [run for run in runs if run.state == 'aborted']
bool_complete = True if finished_runs and not running_runs else False

# emit variables as outputs for other actions
print(f'::set-output name=NUM_FINISHED::{len(finished_runs)}')
print(f'::set-output name=NUM_RUNNING::{len(running_runs)}')
print(f'::set-output name=NUM_CRASHED::{len(crashed_runs)}')
print(f'::set-output name=NUM_ABORTED::{len(aborted_runs)}')
print(f'::set-output name=NUM_BASELINES::{len(baseline_runs)}')
print(f'::set-output name=BOOL_COMPLETE::{bool_complete}')


def summarize_runs(runs, eval_category_label, debug, metrics=[], config_vars=[]):
    """
    Summarize a sequence of wandb runs into a table
    
    Parameters:
    ----------
    runs: a wandb run object
        this is the object you receive when you query a run with the wandb api using the python client
    eval_category_label: str
        this will create a column in the dataframe called __eval.category that = eval_category
    debug: bool
        whether or not to show debuging information
    metrics: List[str]
        metrics names provided as list of strings.  Ex ['accuracy', 'loss']
    config_vars: List[str]
        list of configuration variable names. Ex ['learning_rate', 'num_epochs']
    """
    summary_dict = dict()
    
    for run in runs:
        summary_dict['run.url'] = summary_dict.get('run.url', []) + [run.url]
        summary_dict['run.name'] = summary_dict.get('run.name', []) + [run.name]
        summary_dict['run.tags'] = summary_dict.get('run.tags', []) + [run.tags]
        summary_dict['run.id'] = summary_dict.get('run.id', []) + [run.id]
        summary_dict['run.entity'] = summary_dict.get('run.entity', []) + [run.entity]
        summary_dict['run.project'] = summary_dict.get('run.project', []) + [run.project]
        summary_dict['github_sha'] = summary_dict.get('github_sha', []) + [run.config.get('github_sha')]

        for metric in metrics:
            summary_dict[metric] = summary_dict.get(metric, []) + [run.summary_metrics.get(metric)]
                                                                                                                
        for var in config_vars:            
            # configuration variables preceded with _ to avoid name collisions with metrics
            summary_dict[f"_{var}"] =  summary_dict.get(f"_{var}", []) + [run.config.get(var)]
    
    
    df = pd.DataFrame(summary_dict)
    # debugging information
    if debug:
        logging.debug(f"=== Debugging information for: {eval_category_label} runs ===")
        logging.debug(f"Missing value summary:")
        logging.debug(df.isna().sum())
        logging.debug(f"Preview of Data:")
        logging.debug(df.head(1).T)

    # assign eval_category column
    df['__eval.category'] = eval_category_label
    return df

if finished_runs:
    e_df = summarize_runs(runs=finished_runs, debug=debug, eval_category_label='candidate', metrics=metrics, config_vars=config_vars)
    b_df = summarize_runs(runs=baseline_runs, debug=debug, eval_category_label='baseline', metrics=metrics, config_vars=config_vars)
    df = pd.concat([e_df, b_df])
    report_filename = os.path.join(save_folder, 'wandb_report.csv')
    df.to_csv(report_filename, index=False)
    print(f'{df.shape[0]} runs written to {report_filename}')