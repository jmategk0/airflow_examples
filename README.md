# airflow_exmples
some examples of airflow dags

$ cd /path/to/my/airflow/workspace
$ virtualenv -p `which python3` venv
$ source venv/bin/activate
(venv) $ mkdir airflow_home
(venv) $ export AIRFLOW_HOME=`pwd`/airflow_home
(venv) $ airflow version
(venv) $ airflow initdb

(venv) $ airflow webserver
(venv) $ airflow scheduler

based on http://michal.karzynski.pl/blog/2017/03/19/developing-workflows-with-apache-airflow/
