FROM python:3.7.4

LABEL "com.github.actions.name"="Get Runs From Weights & Biases"
LABEL "com.github.actions.description"="Query a W&B Project for metrics associated with model runs and cache the results for downstream tasks."
LABEL "com.github.actions.icon"="bar-chart-2"
LABEL "com.github.actions.color"="yellow"

RUN pip install wandb tabulate pandas
ENV WANDB_API_KEY=$INPUT_WANDB_API_KEY
ADD wandb_get_runs.py /wandb_get_runs.py
RUN  chmod u+x /wandb_get_runs.py
ENTRYPOINT ["python",  "wandb_get_runs.py"]
