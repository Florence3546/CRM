# coding=utf-8
from fabric.api import run, cd, settings


def install_tools(pkgs):
    run("apt-get install %s" % pkgs)

def compile(url, pkg, ver):
    pkg_name = "%s-%s" % (pkg, ver)
    with cd("/data/tmp"):
        run("wget %s%s.tar.gz" % (url, pkg_name))
        run("tar -zxvf %s.tar.gz" % (pkg_name))

    with cd("/data/tmp/%s" % pkg_name):
        run("./configure")
        run("make && make install")

def install_nginx():
    compile("ftp://ftp.csx.cam.ac.uk/pub/software/programming/pcre/", "pcre", "8.36")
    compile("http://nginx.org/download/", "nginx", "1.8.0")
    run("cp /usr/local/nginx/sbin/nginx /usr/bin") # 将nginx复制到bin目录

def install_nodejs():
    install_tools("curl")
    run("curl -sL https://deb.nodesource.com/setup_4.x | sudo -E bash - ")
    run("apt-get install nodejs")

def pip_install():
    with cd("/data/ztcjl/ztcjl/"):
        run("pip install -r requirements.txt -i %s" % "http://pypi.douban.com/simple/")

def clone_code():
    with cd("/data/ztcjl/"):
        git_url = "git@121.199.162.43:/git/ztcjl"
        run("git clone %s" % git_url)

def ensure_dir(dir):
    with settings(warn_only = True): # 返回为True时，code是1
        run("[ ! -d %s ] && mkdir %s " % (dir, dir))

def ensure_dirs():
    path_list = ["/data", "/data/ztcjl/", "/data/tmp"]
    for path in path_list:
        ensure_dir(path)

def set_env(branch = "master"):
    with cd("/data/ztcjl/ztcjl"):
        # run("git checkout %s" % branch) # 默认分支名是ztcjl5
        run("fab genr_cfg") # 生成配置文件
        run("fab mkdirs") # 生成对应目录
        run("grunt") # 压缩合并静态文件

def change_branch(branch = "master"):
    with cd("/data/ztcjl/ztcjl"):
        run("git checkout %s" % branch)

def do_start():
    run("supervisord -c /etc/supervisord.conf")
    run("nginx")

def install_grunt():
    install_nodejs()
    run("npm install -g grunt-cli")

def do_deploy():
    ensure_dirs()
    run("apt-get update")
    apt_get_list = ["libxml2-dev", "libxslt1-dev"] # for lxml
    apt_get_list.extend(["git", "python-dev", "python-pip", "libmysqld-dev", "libcurl4-openssl-dev", "python-meld3"])
    # libmysqld-dev for python-mysql; libcurl4-openssl-dev for pycurl; python-meld3 for supervisor
    install_tools(' '.join(apt_get_list))
    install_nginx()
    install_grunt()
    clone_code()
    # change_branch()
    pip_install()
    set_env()
    do_start()
