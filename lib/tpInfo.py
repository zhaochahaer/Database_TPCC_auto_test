#!/usr/bin/env python
# -*- coding:UTF-8 -*-
'''
@File    :   tpInof.py
@Time    :   2023/09/05
@Author  :   xin
@Version :   1.0
@Contact :   xin.zhao@esgyn.cn
'''

import configparser
from datetime import datetime

class tpInfo:
    perfoermance_tpcc_path=None
    
    ssh_ip=None
    ssh_port=None
    ssh_name=None
    ssh_passwd = None

    data_path=None
    tableCreates = None
    version_date = None
    package_url = None
    package_name = None
    package_md5_name = None


    def __init__(self):
        sys_config_path = "config/sys_config.ini"
        config = configparser.RawConfigParser()
        config.read(sys_config_path)
        #perfoermance
        self.perfoermance_tpcc_path = config.get('perfoermance','perfoermance_tpcc_path')
        self.flag_name = config.get('perfoermance','flag_path')

        #sshConnection
        self.ssh_ip = config.get('sshConnection','ssh_ip')
        self.ssh_port = config.get('sshConnection','ssh_port')
        self.ssh_name = config.get('sshConnection','ssh_name')
        self.ssh_passwd = config.get('sshConnection','ssh_passwd')

        #database
        self.data_path = config.get('database','data_path')
        self.version_date = config.get('database','version_date')
        self.package_url = config.get('database','package_url')
        self.package_name = config.get('database','package_name')
        self.package_md5_name = config.get('database','package_md5_name')
        self.license = config.get('database', 'license')
        self.mail_list = config.get('database', 'mail_list').split(',')

        #tpcc
        self.tpcc_tableCreates = config.get('tpcc','tableCreates')
        self.tpcc_conn = config.get('tpcc','conn')
        self.tpcc_user = config.get('tpcc','user')
        self.tpcc_password = config.get('tpcc','password')
        self.tpcc_warehouses = config.get('tpcc','warehouses')
        self.tpcc_loadWorkers = config.get('tpcc','loadWorkers')
        self.tpcc_terminals = config.get('tpcc','terminals')
        self.tpcc_runMins = config.get('tpcc','runMins')
        self.tpcc_database = config.get('tpcc','tpcc_database')
        
        #tpcc_run
        self.tpcc_run_threads = config.get('tpcc_run','threads')
        self.tpcc_run_result_directory = config.get('tpcc_run','result_directory')
        self.tpcc_run_result_name_flag = config.get('tpcc_run','result_name_flag')
        self.tpcc_run_data_tpcc_source = config.get('tpcc_run','data_tpcc_source')
        self.tpcc_run_preheat = config.get('tpcc_run','run_preheat')
        self.tpcc_run_number = config.get('tpcc_run','run_number')

        if not self.version_date : 
            self.version_date = datetime.now().strftime('%Y%m%d')

Userinof = tpInfo()