from invoke import task


@task(name="deploy")
def testserver_deploy(c):
    c.run("fab -H root@192.168.56.200 deploy")


@task(name="deploy-grafana")
def testserver_deploy_grafana(c):
    c.run("fab -H root@192.168.56.200 grafana")
