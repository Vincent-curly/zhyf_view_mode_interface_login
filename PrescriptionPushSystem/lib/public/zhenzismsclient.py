import requests
import json
from requests.packages.urllib3.exceptions import InsecureRequestWarning


class ZhenziSmsClient(object):
	def __init__(self, apiUrl, appId, appSecret):
		self.apiUrl = apiUrl
		self.appId = appId
		self.appSecret = appSecret

	def send(self, params):
		data = params
		data['appId'] = self.appId
		data['appSecret'] = self.appSecret
		if ('templateParams' in data) :
			data['templateParams'] = json.dumps(data['templateParams'])
		requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
		response = requests.post(self.apiUrl+'/sms/v2/send.do', data=data, verify=False)
		result = str(response.content, 'utf-8')
		return result

	def balance(self):
		data = {
			'appId': self.appId,
			'appSecret': self.appSecret
		}
		requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
		response = requests.post(self.apiUrl+'/account/balance.do', data=data, verify=False)
		result = str(response.content, 'utf-8')
		return result

	def findSmsByMessageId(self, messageId):
		data = {
			'appId': self.appId,
			'appSecret': self.appSecret,
			'messageId': messageId
		}
		requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
		response = requests.post(self.apiUrl+'/smslog/findSmsByMessageId.do', data=data, verify=False)
		result = str(response.content, 'utf-8')
		return result


if __name__ == '__main__':
	mgclient = ZhenziSmsClient('https://sms_developer.zhenzikj.com', '101856', '6eacf139-384e-4026-ac3e-1dfc5517d452')
	params = {}
	params['number'] = '18687126965'
	params['templateId'] = '8589'
	params['templateParams'] = ['vincent', '云南省精神病医', 'MZ_20200', '处方插入中间！']
	print(mgclient.send(params))
