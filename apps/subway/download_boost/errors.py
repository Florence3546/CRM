# coding=utf-8


class WorkerTimeout(Exception):
    """waiting download worker timeout"""
    pass


class WorkerFailed(Exception):
    """download worker failed"""
    pass


class DownloadFailed(Exception):
    """download contractor failed"""
    pass

