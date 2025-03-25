#otx_feed.py
import requests 
import json
import re
import datetime
import sys
import unidecode
import importlib
import time
import os


import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart

from github import Github

# 系统变量
OTXKEY = os.environ['OTXKEY']
MAIL_NOTICE = os.environ['MAIL_NOTICE']
MAILBOXRECV = os.environ['MAILBOXRECV']
MAILBOXSEND = os.environ['MAILBOXSEND']
MAILPWSEND = os.environ['MAILPWSEND']
MYMAIL1 = os.environ['MYMAIL1']


api_key = OTXKEY
mail_host = 'smtp.qq.com'
dkStart = datetime.datetime.utcnow()
Current_cwd = os.path.abspath(os.path.dirname(__file__))
Mail_List_File = Current_cwd + r'/Mail_list.ini'

'''
proxies = {
    'https' : 'http://127.0.0.1:7890' 
}
'''

# 发送邮件通知
def sendMail(ZIPFILE, text="OTX_FEED_TODAY", error='' ):
	print('发送邮件...')
	timeNow = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
	duration = datetime.datetime.utcnow() - dkStart
	
	#Mail_List = open(Mail_List_File, 'r')#邮件地址列表
	#Mail_List.append(MYMAIL1)
	Mail_To   = []
	Mail_To.append(MYMAIL1)
	#for list in Mail_List:#读取邮件列表文件
	#	Mail_To.extend(list.strip().split(','))
	#Mail_List.close()
	msg = MIMEMultipart() 
	
	msg = MIMEMultipart() 
	Subject = "{0}-{1}".format(time.strftime("%Y%m%d", time.localtime()), text)
	#Content = "{}\n{}\n本次耗时{}秒！".format(timeNow, text, duration)
	#Content = Content + '<br>' + '<br>' + "-----------" + '<br>' + "这是一份自动邮件，请不要回复！！"
	Content = 'otx.alienvault订阅feeds拉取' + '<br>' + '<br>' + "-----------" + '<br>' + "这是一份自动邮件，请不要回复！！"
	msg["Subject"] = Header(Subject, 'utf-8') #邮件标题
	# QQ邮箱使用SMTPLIB 报错550，'The "From" header is missing or invalid. 
	# 详见https://www.zhihu.com/question/414626992/answer/2987902666?utm_id=0
	# 删除utf-8
	# msg["From"] = Header(MAILBOXSEND, 'utf-8')
	msg["From"] = Header(MAILBOXSEND)
	msg["To"] = Header(",".join(Mail_To), 'utf-8')
	msgContent = MIMEText(Content ,'html','utf-8')  #邮件内容
	msgContent["Accept-Language"]="zh-CN"
	msgContent["Accept-Charset"]="ISO-8859-1,utf-8"  
	msg.attach(msgContent)
	attachment = MIMEApplication(open(ZIPFILE,'rb').read()) 
	attachment.add_header('Content-Disposition', 'attachment', filename=os.path.basename(ZIPFILE))  
	msg.attach(attachment)  
	

	try:
		#server = smtplib.SMTP()  #Connection unexpectedly closed
		#server.connect(mail_host, 25) #Connection unexpectedly closed
		server = smtplib.SMTP_SSL(mail_host,465)
		server.login(MAILBOXSEND, MAILPWSEND)
		server.sendmail(MAILBOXSEND, Mail_To, msg.as_string())
		server.quit()
		print("邮件发送成功！")
	except Exception as e:
		print("邮件发送失败！\n{}".format(e))


def upload_file_to_github(
    file_path: str,
    repo_name: str,
    github_token: str,
    branch: str = "main"
) -> None:
    """
    上传文件到 GitHub 仓库（自动处理文本/二进制）
    :param file_path: 本地文件路径
    :param repo_name: 仓库名（如 "user/repo"）
    :param github_token: GitHub Token
    :param target_path: 仓库内目标路径（默认同本地文件名）
    :param branch: 目标分支
    """
    # 确定目标路径
    target_path = os.path.basename(file_path)
    
    # 读取文件内容
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()  # 文本内容
        is_binary = False
    except UnicodeDecodeError:
        with open(file_path, "rb") as f:
            content = base64.b64encode(f.read()).decode("utf-8")  # 二进制内容
        is_binary = True
    
    # 提交到 GitHub
    repo = Github(github_token).get_repo(repo_name)
    try:
        # 尝试更新现有文件
        existing_file = repo.get_contents(target_path, ref=branch)
        repo.update_file(
            path=target_path,
            message=f"Update {os.path.basename(file_path)}",
            content=content,
            sha=existing_file.sha,
            branch=branch
        )
    except Exception:
        # 创建新文件
        repo.create_file(
            path=target_path,
            message=f"Add {os.path.basename(file_path)}",
            content=content,
            branch=branch
        )

if __name__ == "__main__":
	importlib.reload(sys)
	#reload(sys)
	#sys.setdefaultencoding('UTF8')
	if len(api_key.strip())<1:
		print("No api key specified.")
		sys.exit(1)
	now=datetime.datetime.utcnow()
	
	from datetime import date, timedelta
	
	yesterday = (date.today() + timedelta(days=-1)).strftime("%Y-%m-%d")
	#yesterday=datetime.datetime(now.year,now.month, (date.today() + timedelta(days=-1)),now.hour,now.minute,now.second,now.microsecond).isoformat()
	#yesterday=datetime.datetime(now.year,now.month,now.day-1,now.hour,now.minute,now.second,now.microsecond).isoformat()
	
	response=requests.get(
		"https://otx.alienvault.com/api/v1/pulses/subscribed?limit=5000000&modified_since="+yesterday.strip(),
		headers={"X-OTX-API-KEY":api_key} #,proxies=proxies
	)
	#print(response.text)
	jdata=json.loads(response.text)
	ioclist={"domain":[],"ipv4":[],"md5":[],"sha256":[]}
	for p in jdata["results"]:
		for res in p:
			
			#print str(res)+">>>>>>>>>>>>>"+str(p[res])
			name=""
			if "name" in p:
				name=unidecode.unidecode(str(p["name"]))[:128].replace(",",";").replace("\n",";")
			description=""
			if "description" in p:
				description=unidecode.unidecode(str(p["description"]))[:512].replace(",",";").replace("\n",";")
			author=""
			
			if "author" in p:
				author=unidecode.unidecode(str(p["author"]))[:64].replace(",",";").replace("\n",";")
	
			references=""
			if "references" in p:
				if not type(p["references"]) is list:
					references=unidecode.unidecode(str(p["references"]))[:64].replace(",",";").replace("\n",";")
				else:
					refs=';'.join(p["references"][:5]).strip(";")
					references=unidecode.unidecode(refs.replace(",",";").replace("\n",";"))
	
			if "indicators" in res:
				#print r
				for r in p["indicators"]:
					#print r
					#print "**"+res["indicators"]
					output=""
					if "type" in r:
						
						if r["type"] in ["domain","hostname"]:
							ioclist["domain"].append([r["indicator"].strip() ,name,description,author,references])
						elif r["type"].lower().strip() == "filehash-md5":
							ioclist["md5"].append([r["indicator"] ,name,description,author,references])
						elif r["type"].lower().strip() == "filehash-sha256":
							ioclist["sha256"].append([r["indicator"] ,name,description,author,references])
						elif r["type"].lower().strip() == "ipv4":
							ioclist["ipv4"].append([r["indicator"] ,name,description,author,references])
						elif r["type"].lower().strip() == "url":
							m=re.match(r"https?://([\w\d\.\-]*)[\:/]+.*",r["indicator"])
							if not None is m and not None is m.group(1):
								m2=re.match("\d+\.\d+\.\d+\.\d+",m.group(1))
								if not None is m2:
									ioclist["ipv4"].append([m.group(1) ,name,description,author,references])
								else:
									ioclist["domain"].append([m.group(1) ,name,description,author,references])
	filename="ioclist_"+ time.strftime('%Y%m%d', time.localtime(time.time())) +".csv"
	if len(sys.argv)>1 and len(sys.argv[1])>1:
		filename=sys.argv[1]
	with open(filename,"w+") as iocfile:				
		print("IOC Type\tIndicator\tDescription")
		iocfile.write("IOC Type,Indicator,PulseName,Description,Author,References\n")
		lnum=0
		for k in ioclist:
			for e in ioclist[k]:
				lnum+=1
				outputline=','.join(e).strip(",")
				outputline=k+","+outputline+"\n"
				#sys.stdout.write("\rProcessed IOC count:\t"+str(lnum))
				iocfile.write(outputline)
	print("\n")	
	print("\rProcessed IOC count:\t"+str(lnum))
	print("ioc list written to "+ filename)
	filepath = os.getcwd()+'/'+filename
	print(filepath)
	
	sendMail(filepath, "OTX_FEED_TODAY", '' )
	
	#repo_name = os.getenv("GITHUB_REPOSITORY")
	#github_token = os.getenv("GITHUB_TOKEN")
	#upload_file_to_github(filename, 'yusakul/Action_OTX_feed', github_token)

