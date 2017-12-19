import subprocess
import os
import csv
import sqlite3
import glob
from tqdm import *


# hex_text = '0000 006C 0022 0002 015B 00AD 0016 0016 0016 0016 0016 0016 0016 0041 0016 0041 0016 0041 0016 0016 0016 0016 0016 0041 0016 0041 0016 0041 0016 0016 0016 0016 0016 0016 0016 0041 0016 0041 0016 0041 0016 0041 0016 0016 0016 0016 0016 0041 0016 0016 0016 0016 0016 0016 0016 0016 0016 0016 0016 0041 0016 0041 0016 0016 0016 0041 0016 0041 0016 0041 0016 05F7 015B 0057 0016 0E6C'


def check_all_codes():
	tv_files = []
	tv_files = glob.glob('codes/' + '/**/*.csv', recursive=True)
	for file in tqdm(tv_files):
		with open(file, newline='') as f:
			reader = csv.reader(f, delimiter='\n')
			for row in reader:
				row = row[0].split(',')
				if 'function' not in row[0]:
					try:
						if str(row[1]).lower() == 'nec':
							# SOME PROTOCOLS ARE JUST NEC WITHOUT VERSION, THEY SHOULD BE FIRST NEC SO NEC1
							freq, raw_timings = convert_to_raw(convert_to_pronto_hex('NEC1', row[2], row[3], row[4]))
							brand = str(file).split("\\")[1]
							tv_type = str(file).split("\\")[2]
							file_name = str(file).split("\\")[-1].split('.')[0]
							function_name = str(row[0]).upper()
							send_to_db(brand, tv_type, file_name, function_name, freq, raw_timings)
							timings_list.append(raw_timings)
						else:
							freq, raw_timings = convert_to_raw(convert_to_pronto_hex(row[1], row[2], row[3], row[4]))
							brand = str(file).split("\\")[1]
							tv_type = str(file).split("\\")[2]
							file_name = str(file).split("\\")[-1].split('.')[0]
							function_name = str(row[0]).upper()
							send_to_db(brand, tv_type, file_name, function_name, freq, raw_timings)
							timings_list.append(raw_timings)
					except Exception as e:
						pass
		f.close()


def convert_to_pronto_hex(protocol_type, device, subdevice, function):
	with open(os.devnull, 'w') as devnull:
		# SOME ARE GOING OT HAVE PROTOCOLS NOT IN THERE, PROBABLY OLDER AND WE'LL JUST IGNORE THEM
		command = 'irpmaster.bat --decodeir --pronto --name ' + protocol_type + ' D=' + device + ' S=' + subdevice + ' F=' + function
		command = command.split(' ')
		result = subprocess.check_output(command, stderr=devnull)
		result = str(result).split('\\n')[1].strip('\\r')
		return result


def convert_to_raw(pronto_hex_string):
	hex_list = pronto_hex_string.split(' ')
	decimal_list = []
	raw_list = []
	freq_decimal = int(hex_list[1], 16)
	freq = 1000000 / (freq_decimal * .241246)
	for i in range(4):
		del hex_list[0]
	for i in hex_list:
		microSeconds = 1000000 * int(i, 16) / freq
		if microSeconds != 0.0:
			raw_list.append(int(microSeconds))
	for i in hex_list:
		decimal = int(i, 16)
		decimal_list.append(decimal)
	return int(freq), raw_list


def send_to_db(brand, tv_type, filename, function_name, frequency, raw_timing):
	sql_command = "INSERT INTO Remotes (Brand,Type,FileName,FunctionName,Freq,RawTimings) VALUES ('{br}', '{tp}', '{fl}', '{fn}', '{fq}', '{rt}')".format(br=brand, tp=tv_type, fl=filename, fn=function_name, fq=frequency, rt=raw_timing)
	c.execute(sql_command)


if __name__ == '__main__':
	global conn
	global c
	conn = sqlite3.connect('remotes.db')
	c = conn.cursor()
	check_all_codes()
	conn.commit()
	conn.close()
