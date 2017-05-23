# coding=utf-8
import string
import os

from fabric.api import local, lcd, run, cd, task
from fabric.context_managers import env, settings

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def ensure_dir(dir):
    if not os.path.exists(dir):
        os.mkdir(dir)

@task
def syncdb():
    with lcd(BASE_DIR):
        local("python manage.py syncdb")

@task
def mkdirs():
    DATA_ROOT = os.path.dirname(BASE_DIR)
    path_list = ['conf', 'logs']
    for path in path_list:
        print os.path.join(DATA_ROOT, path)
        ensure_dir(os.path.join(DATA_ROOT, path))


class CfgTemplate(object):

    def __init__(self, tmpl_file, dest_file, variables):
        self.tmpl_file = tmpl_file
        self.dest_file = dest_file
        self.variables = variables

    def load_file(self, file_path):
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            return content
        except Exception, e:
            print "load_file error, path=%s, e=%s" % (file_path, e)
            return ''

    def save_file(self, file_path, content):
        try:
            ensure_dir(os.path.dirname(file_path))
            with open(file_path, 'w') as f:
                f.write(content)
            return True
        except Exception, e:
            print "save_cfg error, path=%s, e=%s" % (file_path, e)
            return False

    def __call__(self):
        template = self.load_file(self.tmpl_file)
        if not template:
            raise Exception("tmpl_file does not exist or is empty, path=%s" % self.tmpl_file)

        te = string.Template(template)
        content = te.safe_substitute(self.variables)
        result = self.save_file(self.dest_file, content)
        if not result:
            raise Exception("dest_file save error, check is path exists: %s" % self.dest_file)
        print "genrate config file OK, dest_path=%s" % self.dest_file

@task
def genr_cfg():
    import multiprocessing

    NGINX_CFG_TMPL = os.path.join(BASE_DIR, 'deploy/conf/nginx.conf') # nginx配置模板位置
    NGINX_CFG_FILE = "/usr/local/nginx/conf/nginx.conf" # 默认的nginx配置存放位置

    SUPERVISOR_CFG_TMPL = os.path.join(BASE_DIR, 'deploy/conf/supervisord.conf') # supervisor配置模板位置
    SUPERVISOR_CFG_FILE = "/etc/supervisord.conf" # 默认的supervisord配置存放位置

    def genr_core_list(cores):
        result_list = []
        template = cores * '0'
        for i in reversed(range(cores)):
            result_list.append("%s1%s" % (template[:i], template[i + 1:]))
        return ' '.join(result_list)

    cores = multiprocessing.cpu_count()
    workers = 2 * cores + 1
    core_list = genr_core_list(cores)

    prj_path = BASE_DIR
    log_path = os.path.join(os.path.dirname(prj_path), 'logs')
    try:
        django_path = os.path.dirname(__import__('django').__file__) # 配置django的admin样式的路径
    except:
        django_path = '' # 如果找不到django，就不生成

    variables = {'cores':cores,
                 'workers':workers,
                 'core_list': core_list,
                 'prj_path':prj_path.replace('\\', '/'),
                 'log_path':log_path.replace('\\', '/'),
                 'prj_name':'ztcjl' }

    if django_path:
        variables.update({'django_path':django_path.replace('\\', '/')})

    CfgTemplate(tmpl_file = NGINX_CFG_TMPL, dest_file = NGINX_CFG_FILE, variables = variables)()
    CfgTemplate(tmpl_file = SUPERVISOR_CFG_TMPL, dest_file = SUPERVISOR_CFG_FILE, variables = variables)()

class Server(object):

    def __init__(self, name, cmd_dict):
        self.name = name
        self.start_cmd = cmd_dict.get('start', '')
        self.stop_cmd = cmd_dict.get('stop', '')
        self.restart_cmd = cmd_dict.get('restart', '')

    def __call__(self, oper = "start"):
        if oper == "start":
            local(self.start_cmd)
        elif oper == "restart":
            local(self.restart_cmd)
        elif oper == "stop":
            local(self.stop_cmd)
        else:
            print "wrong command"

class SupervisorServer(Server):

    def __init__(self, name):
        self.name = name
        self.start_cmd = "supervisorctl start %s" % name
        self.stop_cmd = "supervisorctl stop %s" % name
        self.restart_cmd = "supervisorctl restart %s" % name


server = task(SupervisorServer('ztcjl'))
nginx = task(Server('nginx', {'start': 'nginx', 'stop': 'nginx -s stop', 'restart':'nginx -s reload'}))

@task
def grunt(debug = 0):
    if int(debug):
        local("grunt develop")
    else:
        local("grunt")

@task
def update(branch = "master", debug = 0):
    local("git pull origin %s" % branch)
    # grunt(debug)
    server("restart")

@task
def remote():
    env.hosts = []

@task
def update_all(branch = "master"):
    """usage:
    fab remote update_alla
    """
    REMOTE_PATH = "/data/ztcjl/ztcjl"

    with cd(REMOTE_PATH):
        run('fab update:%s' % branch)

@task
def update_timer(branch = "master"):
    run("git pull origin %s" % branch)
    run("supervisorctl restart task")

@task
def start_timer():
    run("supervisorctl start task")

@task
def stop_timer():
    run("supervisorctl stop task")

@task
def update_timer2():
    update_timer()
    run("supervisorctl restart scheduler")

@task
def shutdown_mongo(mongo_role):
    with settings(warn_only = True):
        run("ps -ef | grep %s.conf | grep -v grep | awk '{print $2}' | xargs kill" % mongo_role)

@task
def start_mongo(mongo_role):
    with settings(warn_only = True):
        mongo = 'mongod'
        if mongo_role == "mongos":
            mongo = 'mongos'
        run("%s -f  /mongodb_conf/%s.conf" % (mongo, mongo_role))

@task
def shutdown_web():
    run("supervisorctl stop ztcjl")

@task
def start_web():
    run("supervisorctl start ztcjl")

@task
def shutdown_worker():
    run("killall httpd")

@task
def start_worker():
    run("~/script/start_all_worker.sh")


