from invoke import task


@task(name="dev-start")
def start_development(c):
    r = c.run("sudo docker ps -f name=dev-grafana", hide=True)
    if 'dev-grafana' not in r.stdout:
        print("Starting Grafana")
        c.run("sudo docker run --name=dev-grafana --rm -p 3000:3000 -d grafana/grafana")


@task(name="dev-stop")
def stop_development(c):
    for name in ['dev-grafana']:
        r = c.run(f"sudo docker ps -f name={name}", hide=True)
        if name in r.stdout:
            print(f"Stopping {name}")
            c.run(f"sudo docker stop {name}")


@task(pre=[stop_development], post=[start_development], name="dev-clean")
def cleanup_development(c):
    pass


@task(name="deploy")
def testserver_deploy(c):
    c.run("fab -H root@192.168.56.200 deploy")


@task(name="deploy-grafana")
def testserver_deploy_grafana(c):
    c.run("fab -H root@192.168.56.200 grafana")
