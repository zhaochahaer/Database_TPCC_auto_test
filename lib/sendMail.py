import smtplib
import os
import re
import pandas as pd
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from lib.Logger import logger
from lib.tpInfo import *
from lib.toHtml import *

class SendMail:
    smtpsrvr = "mail.esgyn.cn"  # SMTP server address
    smtpport = 587  # SMTP server port
    username = "publicuser@esgyn.cn"  # SMTP username
    password = "D85vR42tt2"  # SMTP password
    sender = "publicuser@esgyn.cn"  # Sender email address

    # 读取Excel文件
    def read_excel_file(cls):
        logger.info("read_excel_file")
        excel_file_all=os.path.join(os.getcwd(),'html','tpcc',"performance_tpcc_all.xlsx")
        df = pd.read_excel(excel_file_all, sheet_name="summary")
        max_row = df.shape[0]
        # first_row = df.iloc[0, :].tolist()
        if max_row <= 5:
            html_content = df.to_html(index=False)
            return html_content
        else:
            last_five_rows = df.iloc[-5:].to_html(index=False)
            # first_row_html = "<tr>" + "".join([f"<th>{i}</th>" for i in first_row]) + "</tr>"
            return last_five_rows
  
    #读取config\data_config
    def read_data_config(cls):
        logger.info("read_data_config")
        lines=''
        data_config=os.path.join(os.getcwd(),'config',"data_config")
        with open(data_config,'r+') as f:
            for line in f.readlines():
                lines=lines + line + '<br>'
            return lines
        

    #今天耗时对比：
    def today_comparison(cls):
        excel_file_all=os.path.join(os.getcwd(),'html','tpcc',"performance_tpcc_all.xlsx")
        df = pd.read_excel(excel_file_all, sheet_name="summary")


        result = []

        if len(df) <= 2:
            # 如果只有两行或更少，添加相应数量的0到result
            num_columns = len(df.columns) - 3  # 从第4列开始算
            result = [0] * num_columns
        else:
            # 遍历处理每一列
            for i in range(3, len(df.columns)):
                last_value = df.iloc[-1, i]
                second_last_value = df.iloc[-2, i]
                # print(last_value,second_last_value)
                if second_last_value == 0:
                    result.append(0)
                else:
                    comparison_result = (second_last_value - last_value) / second_last_value * 100
                    comparison_result = round(comparison_result, 2)
                    result.append(comparison_result)
        
        return result
    
    def today_text(cls):
        result = cls.today_comparison()
        text_content=""
        thread_nums = re.findall(r'\d+', Userinof.tpcc_run_threads)
        for j in range(len(result)):
            text_content += f"&emsp;今日tpmC：{thread_nums[j]}并发，比较昨天tpmC导入耗时, 性能百分比为：{result[j]}%<br>\n"

        return text_content
    
    def read_email_config(cls):
        email_config = os.path.join(os.getcwd(),'config','email_config')
        with open(email_config,'r+') as f:
            content = f.read()
        
        return content

    # 构建邮件内容
    def make_html_content(cls,excel_file):
        logger.info("make_html_content")
        html_save_file = os.path.join(os.getcwd(),'html','tpcc','{}'.format(Userinof.version_date),'today.html')
        tohtml = to_html(excel_file,html_save_file,"summary")
        html_excel = tohtml.creat_html()
        text_content = cls.today_text()
        hardware_content = cls.read_email_config()

        html_content = f"""
        <html>
        <body>
            Hi all:<br>
            &emsp;TPCC 日常性能基准测试报告如下：<br><br>
            <strong>1.  硬件环境：</strong><br>
            {hardware_content}
            &emsp;f) ip地址：{Userinof.ssh_ip}<br>
            <strong>2.  软件环境：</strong><br>
            &emsp;a)  QianBaseTP数据库daily：{Userinof.version_date}<br>
            &emsp;b)  tpcc版本：1.0.0<br>
            &emsp;c)  表结构：{Userinof.tpcc_tableCreates}<br>
            <strong>3.  数据库配置：</strong><br>{cls.read_data_config()}
            <strong>4.  测试结果：</strong><br>
            &emsp;<strong>a) 近五天测试结果汇总：</strong><br>
            {html_excel}<br>
            
            {text_content}
            &emsp;<strong>b) 详细历史结果：</strong><br>
            &emsp;&emsp;请查看附件：{os.path.basename(excel_file)}<br>

            Best Regards,<br>
            赵鑫<br>
        </body>
        </html>
    """
        return html_content


    def send(cls,excel_file):
        message=cls.make_html_content(excel_file)
        recipient_list=Userinof.mail_list
        subject = f"[{Userinof.version_date}] Test Daily Performance Benchmark of TPCC"
        try:
            server = smtplib.SMTP(cls.smtpsrvr, cls.smtpport)  # Connect to the SMTP server
            server.starttls()  # Start TLS encryption
            server.login(cls.username, cls.password)  # Login to the SMTP server

            msg = MIMEMultipart()  # Create a new email message

            msg["From"] = cls.sender  # Set the sender of the email
            msg["To"] = ", ".join(recipient_list)  # Set the recipients of the email
            msg["Subject"] = subject  # Set the subject of the email

            msg.attach(MIMEText(message, "html"))  # Add the plain text message to the email

            # 添加附件
            with open(excel_file, 'rb') as f:
                attachment = MIMEApplication(f.read(), 'xlsx')
                attachment.add_header('Content-Disposition', 'attachment', filename=os.path.basename(excel_file))
                msg.attach(attachment)

            server.send_message(msg)  # Send the email
            server.quit()  # Disconnect from the SMTP server
            logger.info("Email sent successfully!")
            return True
        except smtplib.SMTPException as e:
            logger.error("An error occurred while sending the email:", e)
            return False

    def send_error_mail(cls,filename):
        # 构建邮件内容
        html_content = f"""
            <html>
            <body>
                Hi all:<br>
                &emsp;<strong style="color:red;">TPCC 日常基准测试失败！请查看附件日志</strong><br>

                Best Regards,<br>
                赵鑫<br>
            </body>
            </html>
        """
        recipient_list=Userinof.mail_list
        subject = f"[{datetime.now().strftime('%Y%m%d')}] Test Daily Performance Fail!!!"
        try:
            server = smtplib.SMTP(cls.smtpsrvr, cls.smtpport)  # Connect to the SMTP server
            server.starttls()  # Start TLS encryption
            server.login(cls.username, cls.password)  # Login to the SMTP server

            msg = MIMEMultipart()  # Create a new email message

            msg["From"] = cls.sender  # Set the sender of the email
            msg["To"] = ", ".join(recipient_list)  # Set the recipients of the email
            msg["Subject"] = subject  # Set the subject of the email

            msg.attach(MIMEText(html_content, "html"))  # Add the plain text message to the email

            # 添加附件
            with open(filename, 'rb') as f:
                attachment = MIMEText(f.read(), 'base64', 'utf-8')
                attachment["Content-Type"] = "application/octet-stream"
                attachment["Content-Disposition"] = f'attachment; filename="{filename}"'
                msg.attach(attachment)

            server.send_message(msg)  # Send the email
            server.quit()  # Disconnect from the SMTP server
            logger.info("Email sent successfully!")
            return True
        except smtplib.SMTPException as e:
            logger.error("An error occurred while sending the email:", e)
            return False
    
mail=SendMail()