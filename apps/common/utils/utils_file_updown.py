# coding:UTF-8
from django.http import HttpResponse
from django.conf import settings

import os
import time


class FileOperateUtil:
    """文件操作工具类，文件上传，下载"""
    def __init__(self):
        pass

    @staticmethod
    def save_single_file(upload_path, file_obj):
        """
        @:description 保存单个文件到服务器
        @:param  upload_path 文件上传存放文件路径名，最终路径：media/传入路径
        @:param  file_obj 待上传文件对象
        """
        # 拆离出文件名和文件格式后缀
        original_name, file_extension = os.path.splitext(file_obj.name)
        # 拼接新的文件名
        filename = "%s_%s%s" % (original_name, time.time(), file_extension)
        # 拼接文件上传目录
        path = "%s%s%s" % (settings.MEDIA_ROOT, "/media/", upload_path)
        # 如果目录不存在，创建此目录
        if not os.path.exists(path):
            os.makedirs(path)
        # 拼接文件上传存放文件路径
        real_path = "%s%s" % (path, filename)
        if not os.path.isfile:
            raise Exception("上传失败，不是一个文件!")
        # 上传文件操作
        destination = open(real_path, 'wb+')
        for chunk in file_obj.chunks():
            destination.write(chunk)
        destination.close()
        file_relative_path = "%s%s%s" % ("/media/", upload_path, filename)
        return file_relative_path

    @staticmethod
    def download_file_util(file_path, file_name=None):
        """
        @:description 下载文件，返回带有文件流的response
        @:param  file_path 待下载文件路径
        @:param  file_name 下载文件名
        """
        real_path = "%s%s" % (settings.MEDIA_ROOT, file_path)
        # 设置响应头
        if os.path.exists(real_path):
            if os.path.isfile(real_path):
                """判断文件是否存在"""
                filename = os.path.basename(real_path)
                # 若未指定下载文件名，则已文件本身名称为准
                if not file_name:
                    file_name = filename
                response = HttpResponse(FileOperateUtil.file_iterator(real_path))
                response['Content_type'] = "application/octet-stream"
                response['Content-Disposition'] = 'attachment; filename={0}'.format(file_name.encode('utf-8'))
            else:
                response = HttpResponse("下载失败,不是一个文件!", content_type="text/plain;charset=utf-8")
        else:
            response = HttpResponse("文件不存在,下载失败!", content_type="text/plain;charset=utf-8")
        return response

    @staticmethod
    def file_iterator(down_file):
        """根据文件路径获取待下载文件流"""
        content = open(down_file, 'rb').read()
        return content
