#!/usr/bin/env python
# -*- coding:UTF-8 -*-
'''
@File    :   downLoad.py
@Time    :   2023/09/05
@Author  :   xin
@Version :   1.0
@Contact :   xin.zhao@esgyn.cn
'''
import os
import shutil
import wget
import hashlib
from lib.tpInfo import *
from lib.Logger import logger

class downLoad:
    def __init__(self):
        self.package_dir = os.path.join(os.getcwd(), 'packages')
        self.package_url = Userinof.package_url.format(Userinof.version_date)
        self.package_name = Userinof.package_name.format(Userinof.version_date)
        self.package_md5_name = Userinof.package_md5_name.format(Userinof.version_date)
        
    def download_daily_package(self):
        package_path = os.path.join(self.package_dir, self.package_name)
        package_md5_path = os.path.join(self.package_dir, self.package_md5_name)

        if os.path.exists(self.package_dir):
            shutil.rmtree(self.package_dir)
        os.makedirs(self.package_dir)

        if not os.path.exists(package_path):
            url = self.package_url + self.package_name
            logger.info(url)
            wget.download(url, package_path)
            logger.info(f"\nDownloaded package: {self.package_name}")

        if not os.path.exists(package_md5_path):
            url_md5 = self.package_url + self.package_md5_name
            wget.download(url_md5, package_md5_path)
            logger.info('Downloaded package md5: {}'.format(self.package_md5_name))

        if self.verify_package_md5(package_path, package_md5_path):
            logger.info("Package verification passed.")
            return True
        else:
            logger.error("Package verification failed.")
            return False

    def verify_package_md5(self, package_path, package_md5_path):
        with open(package_md5_path, 'r') as f:
            md5sum, _ = f.read().split('  ')
        md5 = hashlib.md5(open(package_path, 'rb').read()).hexdigest()
        return md5 == md5sum


download=downLoad()