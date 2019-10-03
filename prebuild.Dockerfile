FROM python:3.7.4

RUN pip install wandb tabulate pandas
COPY wandb_get_runs.py /wandb_get_runs.py
RUN  chmod u+x /wandb_get_runs.py

ENTRYPOINT ["python",  "/wandb_get_runs.py"]
