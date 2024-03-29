from invoke import task
import os
import sys
import json


config_file = 'config_deploy.json'
config = {
    'deploy_host': '',
    'grafana_host': '',
    'nodered_host': ''
}


def config_load():
    if os.path.isfile(config_file):
        config.update(json.loads(open(config_file, 'r').read()))


def config_save():
    open(config_file, 'w').write(json.dumps(config, indent=2))


@task(name="dev-start")
def start_development_locked_versions(c):
    r = c.run("sudo docker ps -f name=dev-grafana", hide=True)
    if 'dev-grafana' not in r.stdout:
        print("Starting Grafana")
        c.run("sudo docker run --name=dev-grafana --rm -p 3000:3000 -d grafana/grafana:8.2.7")
    r = c.run("sudo docker ps -f name=dev-nodered", hide=True)
    if 'dev-nodered' not in r.stdout:
        print("Starting NodeRed")
        c.run("mkdir -p /media/ramdisk/nodered")
        c.run("chown 1000:1000 /media/ramdisk/nodered")
        c.run("sudo docker run --name=dev-nodered --rm -p 1880:1880 -v /media/ramdisk/nodered:/data -d nodered/node-red:2.1.4")


@task(name="dev-start-latest")
def start_development_latest_versions(c):
    r = c.run("sudo docker ps -f name=dev-grafana", hide=True)
    if 'dev-grafana' not in r.stdout:
        print("Starting Grafana")
        c.run("sudo docker run --name=dev-grafana --rm -p 3000:3000 -d grafana/grafana")
    r = c.run("sudo docker ps -f name=dev-nodered", hide=True)
    if 'dev-nodered' not in r.stdout:
        print("Starting NodeRed")
        c.run("mkdir -p /media/ramdisk/nodered")
        c.run("chown 1000:1000 /media/ramdisk/nodered")
        c.run("sudo docker run --name=dev-nodered --rm -p 1880:1880 -v /media/ramdisk/nodered:/data -d nodered/node-red")


@task(name="dev-stop")
def stop_development(c):
    for name in ['dev-grafana', 'dev-nodered']:
        r = c.run(f"sudo docker ps -f name={name}", hide=True)
        if name in r.stdout:
            print(f"Stopping {name}")
            c.run(f"sudo docker stop {name}")
    print('Removing storage for dev-nodered')
    c.run('sudo rm -rf /media/ramdisk/nodered')


@task(pre=[stop_development], post=[start_development_latest_versions], name="dev-clean")
def cleanup_development(c):
    pass


@task(name="deploy")
def deploy(c):
    config_load()
    host = input(f"Host ({config['deploy_host']}): ")
    if host == '' and config['deploy_host'] == '':
        print("invalid input!")
        sys.exit(1)
    if not host == '':
        config['deploy_host'] = host
    c.run(f"fab -H root@{config['deploy_host']} deploy")
    config_save()


@task(name="deploy-grafana")
def deploy_grafana(c):
    config_load()
    if config['grafana_host'] == '' and not config['deploy_host'] == '':
        config['grafana_host'] = config['deploy_host']
    host = input(f"Host ({config['grafana_host']}): ")
    if host == '' and config['grafana_host'] == '':
        print("invalid input!")
        sys.exit(1)
    if not host == '':
        config['grafana_host'] = host
    c.run(f"fab -H root@{config['grafana_host']} grafana")
    config_save()
    select = input('Preconfigure Grafana? (y/n): ')
    if select == 'y':
        preconfigure_grafana(c)


@task(name="deploy-nodered")
def deploy_nodered(c):
    config_load()
    if config['nodered_host'] == '' and not config['deploy_host'] == '':
        config['nodered_host'] = config['deploy_host']
    host = input(f"Host ({config['nodered_host']}): ")
    if host == '' and config['nodered_host'] == '':
        print("invalid input!")
        sys.exit(1)
    if not host == '':
        config['nodered_host'] = host
    c.run(f"fab -H root@{config['nodered_host']} nodered")
    config_save()
    select = input('Preconfigure Node-Red? (y/n): ')
    if select == 'y':
        preconfigure_nodered(c)


@task(name="preconfigure-grafana")
def preconfigure_grafana(c):
    config_load()
    if config['grafana_host'] == '':
        c.run("cd grafana; python preconfiguration.py; cd ..")
    else:
        c.run(f"cd grafana; python preconfiguration.py --host {config['grafana_host']}; cd ..")


@task(name="preconfigure-nodered")
def preconfigure_nodered(c):
    config_load()
    if config['nodered_host'] == '':
        c.run("cd nodered; python preconfiguration.py; cd ..")
    else:
        c.run(f"cd nodered; python preconfiguration.py --host {config['nodered_host']}; cd ..")
