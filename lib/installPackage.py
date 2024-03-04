#!/usr/bin/env python
# -*- coding:UTF-8 -*-
'''
@File    :   installPackage.py
@Time    :   2023/09/05
@Author  :   xin
@Version :   1.0
@Contact :   xin.zhao@esgyn.cn
'''
import os
import signal
from lib.Logger import logger
from lib.tpInfo import *

class InstallPackage:
    def __init__(self,ssh):
        self.ssh_all = ssh
        self.data_path = Userinof.data_path
        self.config_dir = '/home/qianbase'

    def kill_qbasesvr(self):
        logger.info("Killing all qbasesvr processes...")
        cmd = "ps -ef | grep qbasesvr | grep -v grep | awk '{print $2}'"
        for ssh in self.ssh_all:
            stdin, stdout, stderr = ssh.exec_command(cmd)
            process_ids = stdout.read().decode().strip().split("\n")
            for pid_str in process_ids:
                pid_str = pid_str.strip()
                if pid_str.isdigit():
                    pid = int(pid_str)
                    try:
                        os.kill(pid, signal.SIGTERM)
                        logger.info(f"Killed qbasesvr process with PID {pid}")
                    except Exception as e:
                        logger.error(f"Failed to kill qbasesvr process with PID {pid}: {str(e)}")
                        return False
        return True
    
    def check_datebase(self):
        logger.info("check packages")
        cmd = 'rpm -qa | grep QianBaseTP'
        for ssh in self.ssh_all:
            stdin, stdout, stderr = ssh.exec_command(cmd)
            for line in stdout.readlines():
                if 'QianBaseTP' in line:
                    logger.info("uninstall: "+'echo y | rpm -e {}'.format(line))
                    stdin, stdout, stderr = ssh.exec_command('echo y | rpm -e {}'.format(line))
                    for line in stderr.readlines():
                        logger.error("load error:" + line)
                        assert "error" not in line
            logger.info(f"{ssh.get_transport().getpeername()[0]} uninstall Complete!")
        return True
    

    def cleanup_datebase(self):
        for ssh in self.ssh_all:
            cmd = f'mkdir -p {self.data_path} && chown -R qianbase:qianbase {self.data_path} && rm -rf {self.data_path}/* && rm -rf /tmp/.s.QBSQL.20158 && rm -rf /tmp/.s.QBSQL.20158.lock '
            stdin, stdout, stderr = ssh.exec_command(cmd)
            exit_status = stdout.channel.recv_exit_status()
            if exit_status == 0:
                logger.info(f"Cleanup database on {ssh.get_transport().getpeername()[0]} succeeded.")
            else:
                logger.error(f"Cleanup database on {ssh.get_transport().getpeername()[0]} failed with exit code {exit_status}.")
                return False
        
        return True
    

    def write_bashrc(self):
        logger.info("write_bashrc")
        bashrc_path = os.path.join(self.config_dir, '.bashrc')

         # Generate .bashrc content
        content = f'''# .bashrc
# Source global definitions
if [ -f /etc/bashrc ]; then
        . /etc/bashrc
fi
export QBHOME=/usr/local/QianBaseTP
export PATH=${{QBHOME}}/bin:${{PATH}}
export LD_LIBRARY_PATH=${{QBHOME}}/lib

'''
        with open(bashrc_path, 'w') as f:
            f.write(content)

        os.system('chown qianbase:qianbase {}'.format(bashrc_path))


    def install_package(self):
        logger.info("install package:")
        package_dir = os.path.join(os.getcwd(), 'packages')
        package_name = os.path.basename(os.listdir(package_dir)[0])
        cmd = f'echo y | yum install {os.path.join(package_dir, package_name)}'
        if self.check_datebase():
            for ssh in self.ssh_all:
                logger.info(cmd)
                stdin, stdout, stderr = ssh.exec_command(cmd)
                if "Complete!" not in stdout.read().decode():
                    logger.error(stdout.read().decode())
                    return False
                logger.info(f"{ssh.get_transport().getpeername()[0]} install package Complete!")
        return True
    
    
    def install_database(self):
        logger.info("install QianBaseTP database...")
        if self.kill_qbasesvr():
            if self.cleanup_datebase():
                if self.install_package(): 
                    self.write_bashrc()
                    cmd = "su - qianbase --session-command 'qinitdb -D {} -U qianbase'".format(self.data_path)
                    logger.info(cmd)
                    stdin, stdout, stderr = self.ssh_all[0].exec_command(cmd)
                    for line in stdout.readlines():
                        logger.info(line)
                        if "Success. You can now start the database server using" in line:
                            logger.info("数据库安装成功")
                            return True
                    logger.error("数据库初始化失败？？？")
                    return False