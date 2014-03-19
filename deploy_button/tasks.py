from fabric.api import execute
from celery import task


@task()
def deploy():
    try:
        from fabfile import quick_deploy 
        return execute(quick_deploy)
    except Exception as e:
        return 'my_celery_task -- %s' % e.message
