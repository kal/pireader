from fabric.api import cd, local, run


def prepare_deploy():
    local("python pireader/manage.py test reader")
    local("git add -p && git commit")
    local("git push")

def deploy():
    with cd('/home/pi/pireader'):
        run('git pull')
        with cd('/home/pi/pireader/pireader'):
            run('python manage.py migrate reader')
            run('python manage.py test reader')
            run('python manage.py ')