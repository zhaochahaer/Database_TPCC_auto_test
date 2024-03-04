#!/usr/bin/env python
# -*- coding:UTF-8 -*-
'''
@File    :   tpQconfig.py
@Time    :   2023/09/05
@Author  :   xin
@Version :   1.0
@Contact :   xin.zhao@esgyn.cn
'''
import os
import shutil
from lib.Logger import logger
from lib.tpInfo import *
from lib.dataBaseOption import *

class TpQconfig:
    def __init__(self,ssh_all):
        self.ssh = ssh_all
        self.path = Userinof.data_path
        self.data_config_path=os.path.join(os.getcwd(), 'config')
        self.license = Userinof.license
        self.tp_database = Userinof.tpcc_database

    def getConfig(self,path_config):
        with open(path_config,'r+') as f:
            return f.read()

    def create_database(self):
        logger.info("Creating database {}".format(self.tp_database))
        cmd_check = 'su - qianbase -c "qsql -d qianbase -c \\"select datname from qb_database;\\""'
        logger.info(cmd_check)
        stdin, stdout, stderr = self.ssh[0].exec_command(cmd_check)
        if self.tp_database in stdout.read().decode():
            logger.warning("Database tpcc already exists")
            return True
        else:
            cmd_create = 'su - qianbase -c "qcreatedb {}"'.format(self.tp_database)
            stdin, stdout, stderr = self.ssh[0].exec_command(cmd_create)
            for line in stderr.readlines():
                logger.error("Failed to create database {}: ".format(self.tp_database) + line)
                assert "error" not in line
        return True

    def database_qconfig(self):
        data_config_name = os.path.join(self.data_config_path, 'data_config')
        data_config = self.getConfig(data_config_name)
        qianbasetp_conf = os.path.join(self.path,'qianbasetp.conf')

        with open(qianbasetp_conf, 'a') as qianbasetp_file:
            qianbasetp_file.write(data_config)

    def append_qb_hba_conf(self):
        logger.info("append_qb_hba_conf:host all all 0/0 trust")
        hba_path = os.path.join(self.path,'qb_hba.conf')
        with open(hba_path, 'a') as f:
            f.write('host     all         all             0/0            trust\n')


    def replace_license(self):
        license_path = os.path.join(os.getcwd(), 'license')
        license_name = os.path.join(license_path,'license.lic')
        logger.info("license = {}".format(self.license))
        
        if self.license  == 'True' or self.license  == 'true':  
            try:
                dest_share = '/usr/local/QianBaseTP/share/license.lic'
                shutil.copyfile(license_name, dest_share)
                logger.info(f"Copied {license_name} to {dest_share}")

                dest_data = '/data/qianbasetp/license.lic'
                shutil.copyfile(license_name, dest_data)
                logger.info(f"Copied {license_name} to {dest_data}")

                return True
            except Exception as e:
                logger.error(f"Failed to replace license.lic: {str(e)}")
                return False
        else:
            return True
            
    def database_config(self):
        logger.info("database_qconfig...")
        self.append_qb_hba_conf()
        self.database_qconfig()
        dboption=DataBaseOption(self.ssh)
        if self.replace_license(): 
            if dboption.database_qboption('qctl -D {} start'.format(self.path)):
                if self.create_database():
                    logger.info("QianBaseTP database qconfig Complete!")
                    return True

