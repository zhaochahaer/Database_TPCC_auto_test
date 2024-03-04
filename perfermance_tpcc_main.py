
#!/usr/bin/env python
# -*- coding:UTF-8 -*-
'''
@File    :   perfermance_tpcc_main.py
@Time    :   2023/09/05
@Author  :   xin
@Version :   1.0
@Contact :   xin.zhao@esgyn.cn
'''
from datetime import datetime
import time
import schedule
from lib.tpInfo import *
from lib.downLoad import download
from lib.sshClient import *
from lib.installPackage import *
from lib.tpQconfig import *
from lib.dataBaseOption import *
from lib.resultProcess import *
from lib.sendMail import *

class Test:
    def __init__(self,ssh_all):
        self.ssh=ssh_all
        self.tpcc_path = os.path.join(os.getcwd(), 'tool')
        self.tpcc_cnn = Userinof.tpcc_conn
        self.tpcc_user = Userinof.tpcc_user
        self.tpcc_password = Userinof.tpcc_password
        self.tpcc_warehouses = Userinof.tpcc_warehouses
        self.tpcc_loadWorkers = Userinof.tpcc_loadWorkers
        self.tpcc_terminals = Userinof.tpcc_terminals
        self.tpcc_runMins = Userinof.tpcc_runMins
        self.tpcc_tableCreates = Userinof.tpcc_tableCreates
        self.tpcc_database = Userinof.tpcc_database
        self.tpcc_database_path = Userinof.data_path
        self.tpcc_backup_path = Userinof.tpcc_run_data_tpcc_source
        self.tpcc_run_threads = Userinof.tpcc_run_threads
        self.tpcc_run_result_directory = Userinof.tpcc_run_result_directory.format(Userinof.version_date)
        self.tpcc_run_result_name_flag = Userinof.tpcc_run_result_name_flag
        self.tpcc_run_data_tpcc_source = Userinof.tpcc_run_data_tpcc_source
        self.tpcc_run_preheat = Userinof.tpcc_run_preheat
        self.tpcc_run_number = Userinof.tpcc_run_number

    def tpcc_chown(self):
        cmd_chmod = f"chmod 755 {self.tpcc_path} -R"
        cmd_chown = f"chown -R qianbase:qianbase {self.tpcc_path} {self.tpcc_path}/../result -R"

        # Execute the chmod command
        ret_chmod = os.system(cmd_chmod)
        if ret_chmod != 0:
            # handle the error
            logger.error(f"Failed to execute command: {cmd_chmod}")
            return False
        
        # Execute the chown command
        ret_chown = os.system(cmd_chown)
        if ret_chown != 0:
            # handle the error
            logger.error(f"Failed to execute command: {cmd_chown}")
            return False
        # Both commands executed successfully
        logger.info("Permissions updated successfully")
        return True
    
    def tpcc_props(self):
        props_name = os.path.join(self.tpcc_path,'tpcc','benchmarksql','run','props.test')
        props_name_back = os.path.join(self.tpcc_path,'tpcc','benchmarksql','run','props.test.back')
        shutil.copy(props_name_back, props_name)

        with open(props_name, 'r') as props_file:
            lines = props_file.readlines()

        for i in range(len(lines)):
            if lines[i].startswith("conn="):
                lines[i] = f"conn={self.tpcc_cnn}\n"
            if lines[i].startswith("user="):
                lines[i] = f"user={self.tpcc_user}\n"
            if lines[i].startswith("password="):
                lines[i] = f"password={self.tpcc_password}\n"
            if lines[i].startswith("warehouses="):
                lines[i] = f"warehouses={self.tpcc_warehouses}\n"
            if lines[i].startswith("loadWorkers="):
                lines[i] = f"loadWorkers={self.tpcc_loadWorkers}\n"
            if lines[i].startswith("terminals="):
                lines[i] = f"terminals={self.tpcc_terminals}\n"
            if lines[i].startswith("runMins="):
                lines[i] = f"runMins={self.tpcc_runMins}\n"

        with open(props_name, 'w') as props_file:
            props_file.writelines(lines)

    def tpcc_table_log(self):
        tpcc_table_name = os.path.join(self.tpcc_path,'tpcc','benchmarksql','run','runDatabaseBuild.sh')

        with open(tpcc_table_name, 'r') as tpcc_table_name_file:
            lines = tpcc_table_name_file.readlines()
        
        for i in range(len(lines)):
            if lines[i].startswith("BEFORE_LOAD="):
                lines[i] = f"BEFORE_LOAD={self.tpcc_tableCreates}\n"

        with open(tpcc_table_name, 'w') as tpcc_table_name_file:
            tpcc_table_name_file.writelines(lines)


    def tpcc_runDatabaseBuild(self):
        tpcc_build = os.path.join(self.tpcc_path,'tpcc','benchmarksql','run')

        if not self.tpcc_chown():
            logger.error("Failed to set permissions for tpcc folder and files")
            return False

        logger.info("Building tpcc...")
        cmd = f'su - qianbase -c "cd {tpcc_build} && nohup ./runDatabaseBuild.sh props.test |tee tpcc_build_{self.tpcc_warehouses}.log"'
        logger.info(cmd)

        stdin, stdout, stderr = self.ssh[0].exec_command(cmd)
        channel = stdout.channel
        while not channel.exit_status_ready():
            # Only print data when there is data to print
            if channel.recv_ready():
                data = channel.recv(1024)
                logger.info(data.decode('utf-8'), extra={'end': ''})
        stdout.close()
        stderr.close()
        logger.info("TPCC finished Build data")
        return True

    def tpcc_backup_before(self):
        logger.info("tpcc_backup_before...")
        dboption=DataBaseOption(self.ssh)

        if dboption.database_qboption('qsql -d {} -c \"vacuum full;\"'.format(self.tpcc_database)) :
            time.sleep(60)
            if dboption.database_qboption('qsql -d {} -c \"vacuum analyze;\"'.format(self.tpcc_database)):
                time.sleep(120)
                # if dboption.database_qboption('qsql -d {} -c \"checkpoint;\"'.format(self.tpcc_database)):
                if dboption.database_qboption('qsql -c \"checkpoint;\"'):
                    time.sleep(120)
                    # if dboption.database_qboption('qctl stop -D {} -m immediate'.format(self.tpcc_database_path)):
                    os.system('sync')
                    if dboption.database_qboption('qctl -D {} stop'.format(self.tpcc_database_path)):
                        return True
        else:
            return False

    def tpcc_backup(self):
        logger.info(self.tpcc_backup_path)

        try:
            if os.path.exists(self.tpcc_backup_path):
                shutil.rmtree(self.tpcc_backup_path) 

            shutil.copytree(self.tpcc_database_path, self.tpcc_backup_path)

            os.system('chown qianbase:qianbase {} -R'.format(self.tpcc_backup_path))
            logger.info("Backup completed successfully.")
            return True
        except Exception as e:
            logger.error(f"Backup failed: {str(e)}")
            return False


    def tpcc_run_before(self):
        tpcc_run_sh = os.path.join(self.tpcc_path,'tpcc','benchmarksql','run','tpcc_run.sh')
        logger.info("change tpcc_runt.sh:{}".format(tpcc_run_sh))
        try: 
            with open(tpcc_run_sh, 'r') as run_file:
                lines = run_file.readlines()

            for i in range(len(lines)):
                if lines[i].startswith("threads="):
                    lines[i] = f"threads={self.tpcc_run_threads}\n"

            with open(tpcc_run_sh, 'w') as run_file:
                run_file.writelines(lines)
            
            if not os.path.exists(self.tpcc_run_result_directory):
                os.makedirs(self.tpcc_run_result_directory)
            
            # else:
            #     shutil.rmtree(self.tpcc_run_result_directory)
            
            return True
        except Exception as e:
            logger.error("error: {}".format(e))
            return False


    def tpcc_run(self):
        tpcc_run_path = os.path.join(self.tpcc_path,'tpcc','benchmarksql','run')

        if not self.tpcc_chown():
            logger.error("Failed to set permissions for tpcc folder and files")
            return False
    
        logger.info("Running tpcc...")
        cmd = f'su - qianbase -c "cd {tpcc_run_path} && nohup ./tpcc_run.sh {self.tpcc_run_result_directory} {self.tpcc_run_result_name_flag} {self.tpcc_backup_path} {self.tpcc_database_path} {self.tpcc_database} {self.tpcc_warehouses} {self.tpcc_run_preheat} {self.tpcc_run_number}"'
        logger.info(f"Command: {cmd}")

        stdin, stdout, stderr = self.ssh[0].exec_command(cmd)
        channel = stdout.channel
        while not channel.exit_status_ready():
            # Only print data when there is data to print
            if channel.recv_ready():
                data = channel.recv(1024)
                decoded_data = data.decode('utf-8')
                logger.info(decoded_data, extra={'end': ''})

                if "Data inconsistency detected" in decoded_data:
                    logger.error("Data inconsistency detected. Exiting the program.")
                    return False
    
        stdout.close()
        stderr.close()
        logger.info("TPCC finished running")
        return True
    
def run_flag(flag):
    flag_name = Userinof.flag_name

    try:
        with open(flag_name, 'w') as flag_file:
            flag_file.write(flag)
            logger.info(f"Flag '{flag}' has been written to '{flag_name}'")
    except Exception as e:
        logger.error(f"Error writing flag: {e}")

def test_tpcc_main():
        logger.info("Starting TPCC performance testing...")
        try:
            ssh = sshclient.conn(Userinof.ssh_ip,Userinof.ssh_name,Userinof.ssh_passwd,Userinof.ssh_port)
            ssh_all = [ssh]
            
            #download
            if download.download_daily_package():
                logger.info("QianBaseTP_Download completed!")
            else:
                run_flag("1")
                logger.error("QianBaseTP_Download false!!!")
                assert False, "Download false!!!"
            
            #install
            install=InstallPackage(ssh_all)
            if install.install_database():
                logger.info("install Complete!")
            else:
                run_flag("2")
                logger.error("install false!!!")
                assert False, "install false!!!"

            #Configure database parameters
            qconfig = TpQconfig(ssh_all)
            if qconfig.database_config():
                logger.info("configuration Complete!")
            else:
                run_flag("3")
                logger.error("configuration false!!!")
                assert False, "configuration false!"
            
            #Build data
            test = Test(ssh_all)
            test.tpcc_props()
            test.tpcc_table_log()
            if test.tpcc_runDatabaseBuild():
                time.sleep(120)
                logger.info("Build Complete！")
            else:
                run_flag("4")
                logger.error("Build false！！！")
                assert False, "DatabaseBuild false!!!"

            #backup data
            if test.tpcc_backup_before():
                time.sleep(30)
                install.kill_qbasesvr()
                time.sleep(30)
                if test.tpcc_backup():
                    logger.info("backup Complete!")
                else:
                    run_flag("5")
                    logger.error("backup false!!!")
                    assert False,"backup false!!!"
            else:
                run_flag("6")
                logger.error("tpcc_backup_before false!!!")
                assert False,"tpcc_backup_before false!!!"

            #run tpcc
            start_test_time=datetime.now()
            if test.tpcc_run_before():
                if test.tpcc_run():
                    logger.info("run_tpcc Complete!")
                else:
                    run_flag("7")
                    logger.error("run_tpcc false!")
                    assert False, "run_tpcc false!!!"
            
            #Result processing
            resultProcess=ResultProcess()
            list_logs = resultProcess.read_tpcc_log_list()
            excel_file=resultProcess.performance_tpcc_excel(list_logs)
            excel_file_all=resultProcess.performance_tpcc_excel_all(start_test_time,excel_file)

            #send mail
            mail.send(excel_file_all)
            logger.info("Code executed successfully")
        except Exception as e:
            logger.error("An error occurred: {}".format(str(e)))
            mail.send_error_mail(logger.out)
            logger.error("Code execution failed") 

def run_main():
    flag_name = Userinof.flag_name
    
    if os.path.exists(flag_name):
        try:
            with open(flag_name, 'r') as flag_file:
                flag_value = flag_file.read()
                try:
                    flag_value = int(flag_value)
                except ValueError:
                    flag_value = 0

                if flag_value >= 2:
                    logger.info(f"Flag value is {flag_value}, not running test_tpcc_main.")
                else:
                    logger.info(f"Flag value is {flag_value}, running test_tpcc_main.")
                    test_tpcc_main()
        except Exception as e:
            logger.error(f"Error reading flag: {e}")
    else:
        logger.info(f"Flag file '{flag_name}' does not exist, running test_tpcc_main.")
        test_tpcc_main()


if __name__ == '__main__':
    #设置定时任务
    # schedule.every().day.at("20:00").do(run_main)

    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)

    run_main()