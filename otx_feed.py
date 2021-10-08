#otx_feed.py
import requests 
import json
import re
import datetime
import sys
import unidecode
import importlib
import time

api_key="63e1133cb28b2e9a9a9bdc3beda6de712bf320c8252fcf4e251b05bc00454a8b"
'''
proxies = {
    'https' : 'http://127.0.0.1:7890'
}
'''
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
	print("ioc list written to "+filename)