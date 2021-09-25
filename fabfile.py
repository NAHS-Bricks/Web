from fabric import task
import patchwork.transfers
import os

apt_update_run = False
project_dir = "/opt/middleware/nahs/brickweb"
storagedir_grafana = "/var/data/grafana"
grafana_image = 'grafana/grafana'


def docker_pull(c, image):
    print(f"Preloading docker image {image}")
    c.run(f"docker pull {image}")


def docker_prune(c):
    print("Removing all outdated docker images")
    c.run("docker image prune -f")


def systemctl_stop(c, service):
    if c.run(f"systemctl is-active {service}", warn=True, hide=True).ok:
        print(f"Stop Service {service}")
        c.run(f"systemctl stop {service}", hide=True)


def systemctl_start(c, service):
    if not c.run(f"systemctl is-enabled {service}", warn=True, hide=True).ok:
        print(f"Enable Service {service}")
        c.run(f"systemctl enable {service}", hide=True)
    if c.run(f"systemctl is-active {service}", warn=True, hide=True).ok:
        print(f"Restart Service {service}")
        c.run(f"systemctl restart {service}", hide=True)
    else:
        print(f"Start Service {service}")
        c.run(f"systemctl start {service}", hide=True)


def systemctl_start_docker(c):
    if not c.run(f"systemctl is-enabled docker", warn=True, hide=True).ok:
        print(f"Enable Service docker")
        c.run(f"systemctl enable docker", hide=True)
    if c.run(f"systemctl is-active docker", warn=True, hide=True).ok:
        print(f"Service docker allready running")
    else:
        print(f"Start Service docker")
        c.run(f"systemctl start docker", hide=True)


def systemctl_install_service(c, local_file, remote_file, replace_macros):
    print(f"Installing Service {remote_file}")
    c.put(os.path.join('install', local_file), remote=os.path.join('/etc/systemd/system', remote_file))
    for macro, value in replace_macros:
        c.run("sed -i -e 's/" + macro + "/" + value.replace('/', '\/') + "/g' " + os.path.join('/etc/systemd/system', remote_file))


def install_rsyslog(c):
    print("Configuring rsyslog for BrickWeb")
    c.put("install/rsyslog.conf", "/etc/rsyslog.d/brickweb.conf")
    systemctl_start(c, 'rsyslog')


def install_logrotate(c):
    print("Configuring logrotate for BrickWeb")
    c.put("install/logrotate", "/etc/logrotate.d/brickweb")
    c.run("chmod 644 /etc/logrotate.d/brickweb")


def setup_virtualenv(c):
    print("Setup virtualenv for BrickWeb")
    c.run(f"virtualenv -p /usr/bin/python3 {os.path.join(project_dir, 'venv')}")
    print("Installing python requirements for BrickWeb")
    c.run(f"{os.path.join(project_dir, 'venv/bin/pip')} install -r {os.path.join(project_dir, 'requirements.txt')}")


def upload_project_files(c):
    for f in ["brickweb.py", "requirements.txt"]:
        print(f"Uploading {f}")
        c.put(f, remote=os.path.join(project_dir, f))
    for d in ["helpers", "templates", "static"]:
        print(f"Uploading {d}")
        patchwork.transfers.rsync(c, d, project_dir, exclude=['*.pyc', '*__pycache__'])


def create_directorys(c, dirlist):
    for d in dirlist:
        print(f"Creating {d}")
        c.run(f"mkdir -p {d}", warn=True, hide=True)


def install_apt_package(c, package):
    global apt_update_run
    if not c.run(f"dpkg -s {package}", warn=True, hide=True).ok:
        if not apt_update_run:
            print('Running apt update')
            c.run('apt update', hide=True)
            apt_update_run = True
        print(f"Installing {package}")
        c.run(f"apt install -y {package}")
    else:
        print(f"{package} allready installed")


def install_docker(c):
    if not c.run('which docker', warn=True, hide=True).ok:
        print('Install Docker')
        c.run('curl -fsSL https://get.docker.com | sh')
    else:
        print('Docker allready installed')


@task
def deploy(c):
    c.run('hostname')
    c.run('uname -a')
    systemctl_stop(c, 'cron')
    systemctl_stop(c, 'brickweb')
    install_apt_package(c, 'rsync')
    install_apt_package(c, 'python3')
    install_apt_package(c, 'virtualenv')
    create_directorys(c, [project_dir])
    upload_project_files(c)
    setup_virtualenv(c)
    systemctl_install_service(c, 'brickweb.service', 'brickweb.service', [('__project_dir__', project_dir)])
    c.run("systemctl daemon-reload")
    install_rsyslog(c)
    install_logrotate(c)
    systemctl_start(c, 'brickweb')
    systemctl_start(c, 'cron')


@task
def grafana(c):
    c.run('hostname')
    c.run('uname -a')
    install_apt_package(c, 'curl')
    install_docker(c)
    systemctl_start_docker(c)
    docker_pull(c, grafana_image)
    # Timecritical stuff (when service allready runs) - start
    systemctl_stop(c, 'docker.grafana.service')
    create_directorys(c, [storagedir_grafana])
    c.run(f"chmod 777 {storagedir_grafana}")
    systemctl_install_service(c, 'docker.service', 'docker.grafana.service', [('__additional__', ''), ('__storage__', storagedir_grafana + ':/var/lib/grafana'), ('__port__', '3000:3000'), ('__image__', grafana_image)])
    c.run("systemctl daemon-reload")
    systemctl_start(c, 'docker.grafana.service')
    # Timecritical stuff (when service allready runs) - end
    docker_prune(c)
