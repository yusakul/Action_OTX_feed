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


# 系统变量
OTXKEY = os.environ['OTXKEY']
MAIL_NOTICE = os.environ['MAIL_NOTICE']
MAILBOXRECV = os.environ['MAILBOXRECV']
MAILBOXSEND = os.environ['MAILBOXSEND']
MAILPWSEND = os.environ['MAILPWSEND']

api_key = OTXKEY
mail_host = 'smtp.qq.com'
dkStart = datetime.datetime.utcnow()

'''
proxies = {
    'https' : 'http://127.0.0.1:7890'
}
'''

# 发送邮件通知
def sendMail(text="OTX_FEED_TODAY", error='', ZIPFILE):
	print('发送邮件...')
	timeNow = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
	duration = datetime.datetime.utcnow() - dkStart
	content = "{}\n{}\n本次耗时{}秒！".format(timeNow, text, duration)
	msg = MIMEText(content, 'plain', 'utf-8')
	msg["From"] = Header(MAILBOXSEND, 'utf-8')
	msg["To"] = Header(MAILBOXRECV, 'utf-8')
	subject = "{0}-{1}".format(time.strftime("%Y%m%d", time.localtime()), text)
	
	msg["Subject"] = Header(subject, 'utf-8')
	attachment = MIMEApplication(open(ZIPFILE,'rb').read()) 
	attachment.add_header('Content-Disposition', 'attachment', filename=os.path.basename(ZIPFILE))  
	msg.attach(attachment)  
	try:
		server = smtplib.SMTP()
		server.connect(mail_host, 25)
		server.login(MAILBOXSEND, MAILPWSEND)
		server.sendmail(MAILBOXSEND, MAILBOXRECV, msg.as_string())
		server.quit()
		print("邮件发送成功！")
	except Exception as e:
		print("邮件发送失败！\n{}".format(e))
        

if __name__ == "__main__":
	importlib.reload(sys)
	#reload(sys)
	#sys.setdefaultencoding('UTF8')
	if len(api_key.strip())<1:
		print("No api key specified.")
		sys.exit(1)
	now=datetime.datetime.utcnow()
	yesterday=datetime.datetime(now.year,now.month,now.day-1,now.hour,now.minute,now.second,now.microsecond).isoformat()
	
	response=requests.get(
		"https://otx.alienvault.com/api/v1/pulses/subscribed?limit=5000&modified_since="+yesterday.strip(),
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
				sys.stdout.write("\rProcessed IOC count:\t"+str(lnum))
				iocfile.write(outputline)
	print("\n")			
	print("ioc list written to "+ filename)
	
	sendMail("OTX_FEED_TODAY", '', filename)
