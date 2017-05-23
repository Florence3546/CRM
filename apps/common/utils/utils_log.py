# coding=UTF-8

import os, logging.config

import settings

logging.config.fileConfig(os.path.join(settings.PROJECT_ROOT, "logger.conf"))
log = logging.getLogger("infile")
log.info("============== log initialized ==============")
