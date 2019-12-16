#!/usr/bin/env python3.7


# Author: Ricardo Tavares (jose.ricardo.tavares@huawei.com/curupas.gmail.com)
#
# Title: Testa Conectividade em Roteadores 
# Description: This script was developed with Brazilian Portuguese native speakers in mind.
#
# Testa Conectividade is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Testa Conectividade is distributed in the hope that it will be useful,
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

    ssh_username = input("SSH username: ")
    ssh_password = getpass.getpass('SSH Password: ')


    ssh_device = {
    'device_type': 'generic_termserver',
    'ip': ip_addr,
    'username': ssh_username,
    'password': ssh_password,
    'port': 22,
    'secret': ssh_password,
    'global_delay_factor': 2,
    'verbose': True,
    }  

    net_connect = ConnectHandler(**ssh_device)
    print ("SSH prompt: {}".format(net_connect.find_prompt()))


    _header_html="<html>\n"\
                 " <head>\n"\
                 "   <title> Monitoramento de Interfaces</title>\n"\
                 "   <meta http-equiv='refresh' content='10'>\n"\
                 " </head>\n"\
                 "  <body>\n"\
                 "  <h1>Monitoramento de Interfaces</h1>\n"

    with open(args.routers, "r") as file:
       _html_reader = open("Monitoramento.html","w")
       treader = csv.DictReader(file)
       _html_reader.write(_header_html)
       for device_row in treader:
          _html_reader.write("<h2><a href=" + device_row['device_ip'] + '.html> ' + device_row['device_ip'] + "</a><h2>\n<hr>\n")
       _html_reader.write("</body>\n </html>")    
       _html_reader.close()


    with open(args.routers, "r") as file:
        reader = csv.DictReader(file)
        for device_row in reader:
           time.sleep(2)
           net_connect.write_channel("ssh -o StrictHostKeyChecking=no -l " + ssh_username + " " + device_row['device_ip']+'\n' )
           time.sleep(2)
           xxx=net_connect.find_prompt()
           time.sleep(1)
           xxx=net_connect.find_prompt()
           time.sleep(1)
           xxx=net_connect.find_prompt()
           time.sleep(1)
           print("")
           print("")
           print ("Password prompt: {}".format(xxx))
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

           elif((device_row['kind']).capitalize().strip() == "Huawei")  :

              redispatch(net_connect, device_type='generic_termserver')
              net_connect.enable()
              time.sleep(1)
              output = net_connect.find_prompt()
              time.sleep(1)

              time.sleep(1)
              output = net_connect.send_command("display current-configuration | no-more")
              time.sleep(2)

              config = output.split('\n')

              parse=CiscoConfParse(config,comment='#')
              _ping_base="ping -f -c 3 -s 1472 -t 200 "

              
              time.sleep(2)

           else :
              quit()

           interface_cmds = parse.find_objects(r"^interface ")
           IPv4_REGEX = ""
           result = dict()
           result['interfaces'] = dict()

           start_time = timeit.default_timer()

     
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
                for cmd in interface_cmd.re_search_children(r"^ description "):
                    result["interfaces"][intf_name]["description"] = cmd.text.strip()[len("description "):]

                IPv4_REGEX = r"ip\saddress\s(\S+\s+\S+)"

                for cmd in interface_cmd.re_search_children(IPv4_REGEX):
                    ipv4_addr = interface_cmd.re_match_iter_typed(IPv4_REGEX, result_type=IPv4Obj)
                    intf_name = re.split(r'\s+', interface_cmd.text)[-1]
                    #result['interfaces'][intf_name] = dict()
                    result["interfaces"][intf_name].update({
                        "ipv4": {
                            "address": ipv4_addr.ip.exploded,
                            "netmask": ipv4_addr.netmask.exploded
                        }
                    })




           #print(json.dumps(result, indent=4))

# header html
           _header_html="<html>\n"\
                         " <head>\n"\
                         "   <title> Monitoramento de Interfaces</title>\n"\
                         "   <meta http-equiv='refresh' content='10'>\n"\
                         " </head>\n"\
                         "  <body>\n"\
                         "   <h1>" + device_row['device_ip'] + "</h1>\n"

           _body_result= "   <table style='width:100%' align='center'>\n     <col width='250'>\n     <col width='250'>\n     <col width='250'>\n     <col width='250'>\n     <col width='250'>\n     <tr>\n"
           _body_resultb= "     <tr>\n"


           _router_ctr=0

           _html_name = device_row['device_ip'] + ".html"
           _html_reader = open(_html_name,"w")
           _html_reader.write(_header_html)


           for x in result:
             for y in result[x]:
                if(result[x][y]['ipv4']['address']=="0.0.0.0"):
                       continue
                copyfile("aqua ball-jpg", str(y).replace('/','-') + ".jpg")
                _body_result+= "         <td align='center'><img src=" + str(y).replace('/','-')  + ".jpg class='center' style='width=50px;height:50px;'></td>\n" 
                _body_resultb+="         <td align='center'>" + str(y).replace('/','-') + "</td>\n" 
                _router_ctr+=1
                if(_router_ctr >= 5):
                   _html_reader.write(_body_result + "\n     </tr>\n" + _body_resultb + "\n     </tr>\n   </table>\n")
                   _router_ctr=0
                   #_body_result= "\n   <table style='width:100%' align='center'>\n     <tr>\n"
                   _body_result= "   <table style='width:100%' align='center'>\n     <col width='250'>\n     <col width='250'>\n     <col width='250'>\n     <col width='250'>\n     <col width='250'>\n     <tr>\n"
                   _body_resultb= "\n     <tr>\n"

           _html_reader.write(_body_result + "</tr>\n" + _body_resultb + "     </tr>\n   </table>\n  </body>\n </html>")
           _html_reader.close()
           _number_of_checks=1
           _total_checks=1
           if(args.checks is not None):
              _total_checks=int(args.checks)
           while(_number_of_checks <= _total_checks):
             _number_of_checks+=1

             for x in result:
                    print("==================================================================================")
                    print ("Testes de Conectividade " + device_row['device_ip']) 
                    print("==================================================================================")
                    for y in result[x]:
                        if(ipaddress.ip_address(result[x][y]["ipv4"]["address"]) == ipaddress.ip_address("0.0.0.0")):
                            continue
                        z = ipaddress.ip_network(result[x][y]["ipv4"]["address"] + "/" + result[x][y]["ipv4"]["netmask"], strict=False)
                        lz = list(z.hosts())
                        print("-----------------------------------------------------------------------------------------------------")
                        print (device_row['device_ip'] + ": Interface " +
                               y + ' (' + str( ipaddress.ip_interface(result[x][y]["ipv4"]["address"] + "/" + result[x][y]["ipv4"]["netmask"])) + ')')
                        print (result[x][y]["description"])

                        if(len(lz) > 0):
                           print(f'{len(lz):d} hosts - Primeira: {str(lz[0]):s} Última: {str(lz[len(lz)-1]):s}')
                           if(lz[len(lz)-1] == ipaddress.ip_address(result[x][y]["ipv4"]["address"])):
                              if((device_row['kind']).capitalize().strip() == "Cisco")  :
                                    print( "ping " + str(lz[0]) + " count 3 df-bit size 1472 timeout 1" )
                                    output = net_connect.send_command("ping " + str(lz[0]) + " count 3 df-bit size 1472 timeout 1 \n" )
                              elif((device_row['kind']).capitalize().strip() == "Huawei")  :
                                    print( _ping_base + str(lz[0]))
                                    output = net_connect.send_command( _ping_base + str(lz[0]) +"\n" )
                                    if(output.find("Reply") > 0):
                                        print("Interface " + y + " UP")
                                        copyfile("green ball-jpg", str(y).replace('/','-') + ".jpg")
                                    else:
                                        print("Interface " + y + " DOWN")
                                        copyfile("red ball-jpg", str(y).replace('/','-') + ".jpg")
                           else:
                              if((device_row['kind']).capitalize().strip() == "Cisco")  :
                                    print( "ping " + str(lz[len(lz)-1]) + " count 3 df-bit size 1472 timeout 1" )
                                    output = net_connect.send_command( "ping " + str(lz[len(lz)-1]) +" count 3 df-bit size 1472 timeout 1\n" )
                              elif((device_row['kind']).capitalize().strip() == "Huawei")  :
                                    print( _ping_base + str(lz[len(lz)-1]))
                                    output = net_connect.send_command( _ping_base + str(lz[len(lz)-1]) +"\n" )
                                    if(output.find("Reply") > 0):
                                        print("Interface " + y + " UP")
                                        copyfile("green ball-jpg", str(y).replace('/','-') + ".jpg")
                                    else:
                                        print("Interface " + y + " DOWN")
                                        copyfile("red ball-jpg", str(y).replace('/','-') + ".jpg")

                           print(output)
           net_connect.write_channel("quit\n")
 
           print("")
           print("")
           print("==================================================================================")
           print(f"Total de Verificações: {_total_checks:02d}")    
           print("==================================================================================")
           print("")
 
    tseconds =round(timeit.default_timer() - start_geral)
    m, s = divmod(tseconds, 60)
    h, m = divmod(m, 60)
    print ("")
    print (f'Concluído em {h:d}:{m:02d}:{s:02d}')

