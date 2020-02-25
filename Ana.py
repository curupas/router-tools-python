#!/usr/bin/env python3.7
# Author: Ricardo Tavares (jose.ricardo.tavares@huawei.com/curupas.gmail.com)
#
# Ana is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ana is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# If you don't have a copy of the GNU General Public License,
# it is available here <http://www.gnu.org/licenses/>.

# import modules

from netmiko import ConnectHandler
from netmiko import redispatch
from ciscoconfparse import CiscoConfParse
from ciscoconfparse.ccp_util import IPv4Obj
from argparse import ArgumentParser
import ipaddress, json, re, csv, time, timeit, getpass, sys, os
from shutil import copyfile


# main section

if __name__ == "__main__":

    parser = ArgumentParser(description='Arguments for running oneLiner.py', add_help=False)
    parser.add_argument('-r', '--routers', required=True, action='store', help='Lista de roteadores')
    parser.add_argument('-c', '--checks', required=False, action='store', help='Número de verificações')
#    parser.add_argument('-s', '--shutdown', required=False, action='store', help='Exibe interfaces em shutdown')
    parser.add_argument('-h', '--help', action='help', help='Verifica conectividade a partir do elemento de rede indicado')
    args = parser.parse_args()

# trocar para o servidor ssh
    ip_addr = ("10.121.2.61")
    #ip_addr = ("127.0.0.1")
    print("Jump Host", ip_addr)

    start_geral = timeit.default_timer()

    #ssh_username = input("SSH username: ")
    #ssh_password = getpass.getpass('SSH Password: ')
   

    ssh_device = {
    'device_type': 'generic_termserver',
    'ip': ip_addr,
    'username': ssh_username,
    'password': ssh_password,
    'port': 22,
    'secret': ssh_password,
    'global_delay_factor': 3,
    'verbose': True,
    }  

    net_connect = ConnectHandler(**ssh_device)
    print ("SSH prompt: {}".format(net_connect.find_prompt()))

    start_time = timeit.default_timer()
    report=open('report.txt', "w")
    report.write('hostname,slot,1-qtd,2-reservada,3-rotn,4-rota,5-rotd,6-rotrr,7-a1k,8-man,9-rotec,10-rotsh,11-ser,12-e320,13-gerencia,14-descnnhecido,15-downlinks,16,17-percentual,18-intf_name\n')
    with open(args.routers, "r") as file:
        reader = csv.DictReader(file)
        for device_row in reader:
           time.sleep(2)
           net_connect.write_channel("ssh -o StrictHostKeyChecking=no -l " + ssh_username + " " + device_row['device_ip']+'\n' )
           time.sleep(2)
           xxx=net_connect.find_prompt()
           print ("Password prompt: {}".format(xxx))
           time.sleep(1)
           print("")
           print("")
           output = net_connect.read_channel()
           time.sleep(1)
           net_connect.write_channel(net_connect.password + '\n')
           time.sleep(1)
           output += net_connect.read_channel()

           print("")
           print("=============================================================================")
           print("DISPOSITIVO ", (device_row['kind']).capitalize().strip() + "   " + (device_row['device_ip']).upper().strip() )
           print("=============================================================================")
           print("")
           #print(output)

           if((device_row['kind']).capitalize().strip() == "Cisco")  :

              redispatch(net_connect, device_type='cisco_ios')
              net_connect.enable()
              time.sleep(1)
              output = net_connect.find_prompt()
              redispatch(net_connect, device_type='generic_termserver')
              output = net_connect.send_command("terminal len 0")
              time.sleep(1)
              output = net_connect.send_command("show running-config")
              time.sleep(2)

              config = output.split('\n')

              parse=CiscoConfParse(config,comment='#')
              _ping_base="ping "

              time.sleep(2)

           elif((device_row['kind']).capitalize().strip() == "Xr")  :

              redispatch(net_connect, device_type='cisco_xr_ssh')
              net_connect.enable()
              time.sleep(1)
              output = net_connect.find_prompt()
              time.sleep(1)

              redispatch(net_connect, device_type='generic_termserver')
              output = net_connect.send_command("terminal len 0")
              time.sleep(1)
              output = net_connect.send_command("show running-config")
              time.sleep(2)

              config = output.split('\n')

              parse=CiscoConfParse(config,comment='#')
              _ping_base="ping "

              time.sleep(2)

           elif((device_row['kind']).capitalize().strip() == "Huawei")  :

              redispatch(net_connect, device_type='huawei')
              time.sleep(1)
              output = net_connect.find_prompt()

              time.sleep(1)
              output = net_connect.send_command("display current-configuration | no-more")
              time.sleep(2)

              config = output.split('\n')

              time.sleep(1)
              ip_int = net_connect.send_command('display interface brief | i "thernet|100" | no-more')
              #ip_int = ip_int[ip_int.find('VPN') + 5:]
              ip_int = ip_int[ip_int.find('outErrors') + 10:]
              #print("IP INT ",ip_int)
              time.sleep(2)

              parse=CiscoConfParse(config,comment='#')
              _ping_base="ping -f -c 3 -s 1472 -t 200 "

              time.sleep(2)

           else :
              quit()

           interface_cmds = parse.find_objects(r"^interface ")
           IPv4_REGEX = ""
           result = dict()
           result['interfaces'] = dict()

           _uplink, _desconhecido, _reservada, _ser, _rota, _rotec, _rotd=0,0,0,0,0,0,0
           _rotsh, _man, _a1k, _reflector, _e320, _gerencia, _downlink=0,0,0,0,0,0,0
           _ocupadasdownlink=0
           rows, cols = (9, 19) 
           arr = [[0 for i in range(cols)] for j in range(rows)] 

           _sub_int_regex= re.compile(r'd\.\d')
           for interface_cmd in interface_cmds:

                intf_name = interface_cmd.text[len("interface "):]
                result["interfaces"][intf_name] = {}
                result["interfaces"][intf_name]["description"] = "DESCRICAO NAO CONFIGURADA"
                result["interfaces"][intf_name].update({
                    "ipv4": {
                        "address": "0.0.0.0",
                        "netmask": "255.255.255.0"
                    }
                })
                if(device_row['kind'] == 'xr'):
                    IPv4_REGEX = r"ipv4\saddress\s(\S+\s+\S+)"
                else:
                    IPv4_REGEX = r"ip\saddress\s(\S+\s+\S+)"

                for cmd in interface_cmd.re_search_children(r"^ description "):
                    #_description_line= ((cmd.text.strip()).lower())[len('description '):]
                    _description_line= ((cmd.text.strip()).lower())
                    #print(_description_line)
                    #print(interface_cmd.text,cmd.text.strip(), _description_line)
                    result["interfaces"][intf_name]["description"] = cmd.text.strip()[len("description "):]
                    if(re.search(r'\d\.\d',interface_cmd.text) is None):
                        intf_port = re.search('\d/\d/\d',intf_name)
                        if(intf_port is None):
                            continue
                        sub_linha= intf_name
                        slot=(intf_port.group()).split('/')
                        #print(sub_linha[0], intf_port, intf_port.group(), slot[0])
                        if(_description_line.find("reservad") > 0):
                            _reservada+=1
                            _ocupadasdownlink+=1
                            arr[int(slot[0])][2]+=1
                            arr[int(slot[0])][17]+=1
                        elif(_description_line.find("rotn") > 0):
                            _uplink+=1
                            arr[int(slot[0])][3]+=1
                            arr[int(slot[0])][17]+=1
                        elif(_description_line.find("rota") > 0):
                            _rota+=1
                            _ocupadasdownlink+=1
                            arr[int(slot[0])][4]+=1
                            arr[int(slot[0])][17]+=1
                        elif(_description_line.find("rotd") > 0):
                            _rotd+=1
                            _ocupadasdownlink+=1
                            arr[int(slot[0])][5]+=1
                            arr[int(slot[0])][17]+=1
                        elif(_description_line.find("rotrr") > 0):
                            _reflector+=1
                            _ocupadasdownlink+=1
                            arr[int(slot[0])][6]+=1
                            arr[int(slot[0])][17]+=1
                        elif(_description_line.find("a1k") > 0):
                            _a1k+=1
                            _ocupadasdownlink+=1
                            arr[int(slot[0])][7]+=1
                            arr[int(slot[0])][17]+=1
                        elif(_description_line.find("man") > 0):
                            _man+=1
                            _ocupadasdownlink+=1
                            arr[int(slot[0])][8]+=1
                            arr[int(slot[0])][17]+=1
                        elif(_description_line.find("rotec") > 0):
                            _rotec+=1
                            _ocupadasdownlink+=1
                            arr[int(slot[0])][9]+=1
                            arr[int(slot[0])][17]+=1
                        elif(_description_line.find("rotsh") > 0):
                            _rotsh+=1
                            _ocupadasdownlink+=1
                            arr[int(slot[0])][10]+=1
                            arr[int(slot[0])][17]+=1
                        elif(_description_line.find("ser") > 0):
                            _ser+=1
                            _ocupadasdownlink+=1
                            arr[int(slot[0])][11]+=1
                            arr[int(slot[0])][17]+=1
                        elif(_description_line.find("e320") > 0):
                            _e320+=1
                            _ocupadasdownlink+=1
                            arr[int(slot[0])][12]+=1
                            arr[int(slot[0])][17]+=1
                        elif(_description_line.find("gerencia") > 0):
                            _gerencia+=1
                            _ocupadasdownlink+=1
                            arr[int(slot[0])][13]+=1
                            arr[int(slot[0])][17]+=1
                        else:
                            _desconhecido+=1
                            _ocupadasdownlink+=1
                            arr[int(slot[0])][14]+=1
                            arr[int(slot[0])][17]+=1


                 

                for cmd in interface_cmd.re_search_children(IPv4_REGEX):
                    ipv4_addr = interface_cmd.re_match_iter_typed(IPv4_REGEX, result_type=IPv4Obj)
                    intf_name = re.split(r'\s+', interface_cmd.text)[-1]
                    result["interfaces"][intf_name].update({
                        "ipv4": {
                            "address": ipv4_addr.ip.exploded,
                            "netmask": ipv4_addr.netmask.exploded
                        }
                    })
                #print(intf_name, result['interfaces'][intf_name]['description']) 
                if(intf_name.find('thernet') > 0):
                   intf_port = re.search('\d/\d/\d',intf_name)
                   sub_linha= intf_name
                   slot=(intf_port.group()).split('/')
                   zzz=result['interfaces'][intf_name]['description']
                   #print(slot, zzz)
                   if((zzz.find('CONFIG') > 0)  and (re.search(r'\d\.\d',interface_cmd.text) is None) ):
                                 #print("aqui")
                                 _downlink+=1
                                 arr[int(slot[0])][15]+=1

           #print(ip_int)         
           _ip_int_line=ip_int.split('\n')
           print('qtd reservada rotn rota rotd rotrr a1k man rotec rotsh ser e320 gerencia descnnhecido 14 downlinks ocupa_down 17 ocupa_slot intf_name')
           _total_ports=0
           for line_ctr in range(0,len(_ip_int_line) - 1):
               if(re.search('/\d\.\d', _ip_int_line[line_ctr]) is not None):
                   continue

               _interface=(_ip_int_line[line_ctr]).split()
               intf_name = re.search('\d/\d/\d',_interface[0])
               intf_port = re.search('\d/\d/\d.*',_interface[0])
               #print(intf_name, intf_port)
               if((intf_port.group()).find('(10G') > 0 ):
                   _int_trail='(10G)'
               else:
                   _int_trail=''
               _pos = (_interface[0]).find(intf_port.group())
               #print(intf_port.group(), _interface[0],_pos, zzz)
               arr[int(slot[0])][0]=str(_interface[0][0:_pos]) + _int_trail
               sub_linha= (_interface)
               #print(slot)
               slot=(intf_name.group()).split('/')
               #print(sub_linha[0], intf_name, intf_name.group(), slot[0])
               arr[int(slot[0])][1]+=1
               _total_ports+=1
               #print(line_ctr, _ip_int_line[line_ctr])
               #print(_interface)
               #arr[int(slot[0])][15]=intf_name[0:intf_port.span()[0]] 
           ctr=0
 
           for row in arr: 
               if(row[1] > 0):
                   row[18]= (float(row[17])/float(row[1])) * 100.0
               else:
                   row[18]=0.0

           for row in arr: 
               print(f"Slot {ctr:1d}: ", end='')
               report.write(f"{device_row['device_ip']},{ctr:1d},")
               for col in range(1,18):
                   if(col == 17):
                      print((str(f'{row[col]:02.2f}').zfill(5)) + '%', end=' - ') 
                      report.write((str(f'{row[col]:02.2f},').zfill(5))) 
                   else:
                      print(f'{row[col]:2d}', end=' - ') 
                      report.write(f'{row[col]:2d},') 
               print(f"{row[0]}")
               report.write(f"{row[0]}\n")
               ctr+=1
           #print(json.dumps(result, indent=4))
           time.sleep(1)
           net_connect.write_channel("quit\n" )
           time.sleep(1)
           report.write(f'{device_row["device_ip"]},,{_total_ports:02d},{_reservada:02d},{_uplink:02d},{_rota:02d},{_rotd:02d},{_reflector:02d},{_a1k:-2d},{_man:02d},{_rotec:02d},{_rotsh:02d},{_ser:02d},{_e320:02d},{_gerencia:02d},{_desconhecido:02d},{_ocupadasdownlink + _uplink:02d},,{((_ocupadasdownlink + _uplink)/_total_ports) * 100:02.2f}\n')

           print("")
           print (f'ROTN:{_uplink:02d} Refletores:{_reflector:02d} ROTD:{_rotd:02d} Portas Reservadas:{_reservada:02d}')
           print ("")
           print (f'ROTA:{_rota:02d} ROTEC:{_rotec:02d} ROTSH:{_rotsh:02d} SER:{_ser:02d} MAN:{_man:02d} A1K:{_a1k:02d} E320:{_e320:02d} Gerências:{_gerencia:02d} Não classficados:{_desconhecido:02d}')
           print ("")
           print (f'Total de Downlinks - incluindo não classificados: {_ocupadasdownlink:02d}')
           print ("")
           print (f'Portas:{_total_ports:02d} ')
           print ("")
           print (f'Percentual de uso de portas: {((_ocupadasdownlink + _uplink)/_total_ports) * 100:02.2f}')
           print ("")


    tseconds =round(timeit.default_timer() - start_geral)
    m, s = divmod(tseconds, 60)
    h, m = divmod(m, 60)

    report.close()
    print (f'Concluído em {h:d}:{m:02d}:{s:02d}')

