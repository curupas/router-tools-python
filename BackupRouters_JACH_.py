#!/usr/bin/env python3.7
# Author: Ricardo Tavares (jose.ricardo.tavares@huawei.com/curupas.gmail.com)
#
# Title: Backup Routers
# Description: Python script to read Cisco/Alcatel/Huawei/Juniper configuration and save acopy (backup)
# Description: This script was developed with Brazilian Portuguese native speakers in mind.
# Description: This script uses a jumphost to reach each device.
#
# Backup Routers is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Backup Routers is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# If you don't have a copy of the GNU General Public License,
# it is available here <http://www.gnu.org/licenses/>.


from netmiko import ConnectHandler
from netmiko import redispatch
from argparse import ArgumentParser
import csv, time, timeit, sys, os, getpass

if __name__ == "__main__":
    parser = ArgumentParser(description='Arguments for running oneLiner.py')
    parser.add_argument('-r', '--routers', required=True, action='store', help='Routers')
    args = parser.parse_args()

    #Jump Host IP Address

    ip_addr = ("10.121.2.8")
    #ip_addr = ("127.0.0.1")

    print ("Jump Host: " + ip_addr)
    #ssh_username = input("SSH username: ")
    #ssh_password = getpass.getpass('SSH Password: ')
    ssh_username = "tr694869"
    ssh_password = "Qrawtro9"


    ssh_device = {
    'device_type': 'generic_termserver',
    'ip': ip_addr,
    'username': ssh_username,
    'password': ssh_password,
    'secret': ssh_password,
    'port': 22,
    'global_delay_factor': 3,
    }  

    net_connect = ConnectHandler(**ssh_device)
    print ("SSH prompt: {}".format(net_connect.find_prompt()))
    start_time = timeit.default_timer()

    with open(args.routers, "r") as file:
        reader = csv.DictReader(file)

        for device_row in reader:
           _bkp_name = device_row['device_ip'] + ".bkp"
           _bkp_reader = open(_bkp_name,"w")
          
           if((device_row['port']).strip() == "23")  :
              net_connect.write_channel("telnet "+device_row['device_ip']+'\n' )
           else:
               net_connect.write_channel("ssh -o GSSAPIAuthentication=no -o StrictHostKeyChecking=no " + ssh_username + "@"+device_row['device_ip']+'\n' )


           time.sleep(2)
           output = net_connect.read_channel()
           time.sleep(1)
           if((device_row['port']).strip() == "23")  :
              net_connect.write_channel(net_connect.username + '\n')
              time.sleep(1)
           net_connect.write_channel(net_connect.password + '\n')
           time.sleep(1)
           output += net_connect.read_channel()
           print(output)

           print("DISPOSITIVO ", (device_row['kind']).capitalize().strip())
           print(output)
           time.sleep(1)


           if((device_row['kind']).capitalize().strip() == "Cisco")  :

               redispatch(net_connect, device_type='cisco_ios')
               net_connect.enable()
               time.sleep(1)
               redispatch(net_connect, device_type='generic_termserver')
               output = net_connect.find_prompt()
               print (output)
               output = net_connect.send_command("term len 0")
               print (output)
               time.sleep(1)
               output = net_connect.send_command("show running")
               print (output)
               _bkp_reader.write(output)

           if((device_row['kind']).capitalize().strip() == "Xr")  :

               redispatch(net_connect, device_type='cisco_xr')
               net_connect.enable()
               time.sleep(1)
               redispatch(net_connect, device_type='generic_termserver')
               output = net_connect.find_prompt()
               print (output)
               output = net_connect.send_command("term len 0")
               print (output)
               time.sleep(1)
               output = net_connect.send_command("show running")
               print (output)
               _bkp_reader.write(output)

           elif((device_row['kind']).capitalize().strip() == "Huawei")  :

               redispatch(net_connect, device_type='generic_termserver')
               #net_connect.enable()
               time.sleep(1)
               output = net_connect.find_prompt()
               print (output)
               output = net_connect.send_command('display current-configuration | no-more')
               print (output)
               time.sleep(1)
               _bkp_reader.write(output)

           elif((device_row['kind']).capitalize().strip() == "Nokia")  :

               #redispatch(net_connect, device_type='alcatel_sros_ssh')
               redispatch(net_connect, device_type='generic_termserver')
               net_connect.enable()
               output = net_connect.find_prompt()
               print (output)
               time.sleep(1)
               output = net_connect.send_command('environment no more')
               print (output)
               output = net_connect.send_command('admin display-config')
               print (output)
               time.sleep(2)
               print (output)
               _bkp_reader.write(output)

           elif((device_row['kind']).capitalize().strip() == "Juniper")  :

               redispatch(net_connect, device_type='generic_termserver')
               #net_connect.enable()
               time.sleep(1)
               output = net_connect.find_prompt()
               print (output)
               output = net_connect.send_command('show configuration | no-more')
               print (output)
               time.sleep(1)
               _bkp_reader.write(output)

           if((device_row['kind']).capitalize().strip() == "Nokia")  :
               net_connect.write_channel("logout\n" )
           else:
               net_connect.write_channel("quit\n" )
           time.sleep(3)
			
        _bkp_reader.close()

        print (f'Concluído em {timeit.default_timer() - start_time:.3f} segundos')

