
#!/usr/bin/env python
# -*- coding:UTF-8 -*-
'''
@File    :   dataBaseOption.py
@Time    :   2023/09/05
@Author  :   xin
@Version :   1.0
@Contact :   xin.zhao@esgyn.cn
'''
import os
from lib.Logger import logger

class DataBaseOption:
    def __init__(self,ssh_all):
        self.ssh = ssh_all
        self.option_log = os.path.join(os.getcwd(), 'log')

    def database_qboption(self, option):
        log_file = os.path.join(self.option_log,'qctl_output.txt')
        cmd = "su - qianbase --session-command '{}' > {} 2>&1".format(option,log_file)
        # if "start" in option:
        #     cmd = "su - qianbase --session-command '{}' > {} 2>&1".format(option,log_file)
        # elif "stop" in option:
        #     cmd = "su - qianbase --session-command '{}' > {} 2>&1".format(option,log_file)
        # elif "full" in option:
        #     cmd = "su - qianbase --session-command '{}' > {} 2>&1".format(option,log_file)
        # elif "analyze" in option:
        #     cmd = "su - qianbase --session-command '{}' > {} 2>&1".format(option,log_file)
        # else:
        #     logger.error("Invalid option")
        #     return False
        
        logger.info("{} ...".format(cmd))
        try:
            stdin, stdout, stderr = self.ssh[0].exec_command(cmd, timeout=300)
            
            exit_code = stdout.channel.recv_exit_status()

            if exit_code == 0:
                logger.info("Command executed successfully")
            else:
                logger.error("Command failed with exit code {}".format(exit_code))

            with open(log_file, 'r') as log:
                log_output = log.read()
                logger.info("Command Output:")
                logger.info(log_output)

                if "server started" in log_output:
                    logger.info("QianBaseTP Database successfully started Complete!")
                    return True
                elif "server stopped" in log_output:
                    logger.info("QianBaseTP Database successfully shutdown Complete!")
                    return True
                elif "VACUUM" in log_output:
                    logger.info("QianBaseTP Database successfully : {}".format(option))
                    return True
                elif "CHECKPOINT" in log_output:
                    logger.info("QianBaseTP Database successfully : {}".format(option))
                    return True
                else:
                    logger.error("{} database TP failed".format(option))
                    return False

        except Exception as e:
            logger.error("An error occurred: {}".format(e))
            return False