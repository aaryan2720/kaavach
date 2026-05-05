import requests
p={'features':{'proto':'tcp','service':'-','state':'REQ_RST','dur':2.0,'spkts':50,'dpkts':1,'sbytes':5000,'dbytes':100,'rate':500,'sttl':64,'dttl':0}}
r=requests.post('http://localhost:8000/predict', json=p, timeout=10)
print('predict', r.status_code, r.text)
print('debug last:', requests.get('http://localhost:8000/debug/last_predict', timeout=10).text)
