import requests
import binascii
r = requests.get('https://eospark.com/api/v2/contract/epsdcclassic/history')
# r = requests.get('https://eospark.com/api/v2/contract/nkpaymentcap/history')
# r = requests.get('https://eospark.com/api/v2/contract/eoscastdmgb1/history')
# r = requests.get('https://eospark.com/api/v2/contract/eoslotsystem/history')
# r = requests.get('https://eospark.com/api/v2/contract/xlotoioeosio/history')
# r = requests.get('https://eospark.com/api/v2/contract/eosbetdice11/history')

entries = r.json()['data']
memos = list(entry['memo'] for entry in entries)
for m in memos:
	r = requests.get('https://eospark.com/api/v2/transaction/' + m + '/rawdata')
	actions = r.json()['data']['raw_data']['trx']['transaction']['actions']
	code = actions[0]['data']['code']
	print(len(code))
	if len(code):
		fileName = "EosParkData/" + actions[0]['data']['account'] + "_" + r.json()['data']['timestamp'] + "_" + str(r.json()['data']['block_num']) + ".wasm"
		with open(fileName, 'wb') as f:
			for i in range(0, len(code)):
				if i%2 == 0:
					# print(code[i: i+2])
					f.write(
						binascii.unhexlify(code[i: i+2])
					)