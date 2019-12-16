#!/usr/bin/env python3.7^M
# Author: Ricardo Tavares (jose.ricardo.tavares@huawei.com/curupas.gmail.com)^M
#^M
# Title: Executa Comandos em Roteadores v1.1^M
# Description: Python script to execute op commands.^M
# Description: This script was developed with Brazilian Portuguese native speakers in mind.^M
#^M
# Executa Comando em  Roteadores is distributed in the hope that it will be useful,^M
# but WITHOUT ANY WARRANTY; without even the implied warranty of^M
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the^M
# GNU General Public License for more details.^M
#^M
# If you don't have a copy of the GNU General Public License,^M
# it is available here <http://www.gnu.org/licenses/>.^M
^M
from netmiko import ConnectHandler
from netmiko import redispatch
from argparse import ArgumentParser
import csv, getpass,sys, os, time, timeit, datetime

#define JUMPHOST "10.121.2.61"

if __name__ == "__main__":

    parser = ArgumentParser(description='Arguments for running oneLiner.py', add_help=False)
    parser.add_argument('-r', '--routers', required=True, action='store', help='Lista de Roteadores')
    parser.add_argument('-c', '--cisco', action='store', help='Lista de Comandos Cisco')
    parser.add_argument('-u', '--huawei', action='store', help='Lista de Comandos Huawei')
    parser.add_argument('-n', '--nokia', action='store', help='Lista de Comandos Nokia/Alcatel')
    parser.add_argument('-j', '--juniper', action='store', help='Lista de Comandos Juniper')
    parser.add_argument('-h', '--help', action='help', help='Todos os parâmetros são obrigatórios')
    args = parser.parse_args()

    if(args.cisco is None):
            print("\nATENÇÃO! Usando Cisco.cmd como arquivo de comandos")
            args.cisco="Cisco.cmd"

    if(args.huawei is None):
            print("\nATENÇÃO! Usando Huawei.cmd como arquivo de comandos")
            args.huawei="Huawei.cmd"

    if(args.nokia is None):
            print("\nATENÇÃO! Usando Nokia.cmd como arquivo de comandos")
            args.nokia="Nokia.cmd"

    if(args.juniper is None):
            print("\nATENÇÃO! Usando Juniper.cmd como arquivo de comandos")
            args.juniper="Juniper.cmd"

    with open(args.cisco,"r") as Cisco_cmd:
         Cisco_Cmd_Set=Cisco_cmd.readlines()
         LenCiscoSet=len(Cisco_Cmd_Set)
         print("")
         print("Serão executados " + str(len(Cisco_Cmd_Set)) + " comandos em roteadores do tipo CISCO")
         print("===============================================================")
         for commands in range(0,LenCiscoSet):
             print((Cisco_Cmd_Set[commands]).replace("\n",""))
         print("===============================================================")

    with open(args.huawei,"r") as Huawei_cmd:
         Huawei_Cmd_Set = Huawei_cmd.readlines()
         LenHuaweiSet=len(Huawei_Cmd_Set)
         print("")
         print("Serão executados " + str(len(Huawei_Cmd_Set)) + " comandos em roteadores do tipo HUAWEI")
         print("===============================================================")
         for commands in range(0,LenHuaweiSet):
             print((Huawei_Cmd_Set[commands]).replace("\n",""))
         print("===============================================================")

    with open(args.nokia,"r") as Nokia_cmd:
         Nokia_Cmd_Set = Nokia_cmd.readlines()
         LenNokiaSet=len(Nokia_Cmd_Set)
         print("")
         print("Serão executados " + str(len(Nokia_Cmd_Set)) + " comandos em roteadores do tipo NOKIA")
         print("===============================================================")
         for commands in range(0,LenNokiaSet):
             print((Nokia_Cmd_Set[commands]).replace("\n",""))
         print("===============================================================")

    with open(args.juniper,"r") as Juniper_cmd:
         Juniper_Cmd_Set = Juniper_cmd.readlines()
         LenJuniperSet=len(Juniper_Cmd_Set)
         print("")
         print("Serão executados " + str(len(Juniper_Cmd_Set)) + " comandos em roteadores do tipo JUNIPER")
         print("===============================================================")
         for commands in range(0,LenJuniperSet):
             print((Juniper_Cmd_Set[commands]).replace("\n",""))
         print("===============================================================")

    print("")

    #ssh_username = input("SSH username: ")
    #ssh_password = getpass.getpass('SSH Password: ')
    ssh_username = "tr694869"
    ssh_password = "Qrawtro9"

    ip_addr = ("10.121.2.8")

    ssh_device = {
    'device_type': 'generic_termserver',
    'ip': ip_addr,
    'username': ssh_username,
    'password': ssh_password,
    'port': 22,
    'global_delay_factor': 2,
    }  

    net_connect = ConnectHandler(**ssh_device)
    print ("SSH prompt: {}".format(net_connect.find_prompt()))

    start_geral = timeit.default_timer()
    data_hoje = datetime.date.today()

    report_file=open("report.txt","w")
    print("Data: ", data_hoje)
    report_file.write("Data: " + str(data_hoje) + "\n")
    with open(args.routers, "r") as file:
        reader = csv.DictReader(file)
        device_cnt = 0
        for device_row in reader:

           _bkp_name = device_row['device_ip'] + ".ana"
           _bkp_reader = open(_bkp_name,"w")
 
           device_cnt = device_cnt +1

           net_connect.write_channel("ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no " + ssh_username  + "@"+device_row['device_ip']+'\n' )
           time.sleep(2)
           print ("Password prompt: {}".format(net_connect.find_prompt()))
           time.sleep(2)
           output = net_connect.read_channel()
           time.sleep(1)
           net_connect.write_channel(net_connect.password + '\n')
           time.sleep(1)
           time.sleep(1)
           output += net_connect.read_channel()

           print("")
           print("=============================================================================")
           print("DISPOSITIVO ", (device_row['kind']).capitalize().strip() + "   " + (device_row['device_ip']).upper().strip() )
           print("=============================================================================")
           print("")
           print(output)

           report_file.write("\n")
           report_file.write("=============================================================================\n")
           report_file.write("DISPOSITIVO: " + (device_row['kind']).capitalize().strip() + "   " + (device_row['device_ip']).upper().strip() )
           report_file.write("\n=============================================================================\n")
           report_file.write("\n")

           redispatch(net_connect, device_type='generic_termserver')
           output = net_connect.find_prompt()
           print (output)
           time.sleep(2)

           if((device_row['kind']).capitalize().strip() == "Cisco")  :

                   for commands in range(0,LenCiscoSet):
                       output = net_connect.send_command((Cisco_Cmd_Set[commands]))
                       print("")
                       print("=============================================================")
                       print((Cisco_Cmd_Set[commands]).replace("\n",""))
                       print("=============================================================")
                       print (output)

                       time.sleep(2)

                       _bkp_reader.write(output)

           elif((device_row['kind']).capitalize().strip() == "Huawei") :

                   redispatch(net_connect, device_type='generic_termserver')
                   for commands in range(0,LenHuaweiSet):
                       output = net_connect.send_config_set((Huawei_Cmd_Set[commands]).replace("\n",""))
                       print("")
                       print("=============================================================")
                       print((Huawei_Cmd_Set[commands]).replace("\n",""))
                       print("=============================================================")
                       print (output)

                       report_file.write("\n")
                       report_file.write("\n=============================================================\n")
                       report_file.write((Huawei_Cmd_Set[commands]))
                       report_file.write("=============================================================\n")
                       report_file.write(output)
                       time.sleep(2)

                       _bkp_reader.write(output)

           elif((device_row['kind']).capitalize().strip() == "Nokia") :

                   for commands in range(0,LenNokiaSet):
                       output = net_connect.send_command((Nokia_Cmd_Set[commands]).replace("\n",""))
                       print("")
                       print("=============================================================")
                       print((Nokia_Cmd_Set[commands]).replace("\n",""))
                       print("=============================================================")
                       print (output)
                       time.sleep(1)

                       _bkp_reader.write(output)

           elif((device_row['kind']).capitalize().strip() == "Juniper") :

                   for commands in range(0,LenJuniperSet):
                       output = net_connect.send_command((Juniper_Cmd_Set[commands]).replace("\n",""))
                       print("")
                       print("=============================================================")
                       print((Juniper_Cmd_Set[commands]).replace("\n",""))
                       print("=============================================================")
                       print (output)
                       time.sleep(1)

                       _bkp_reader.write(output)

           time.sleep(2)
           if((device_row['kind']).capitalize().strip() == "Nokia") :
               net_connect.write_channel("logout\n" )
           else:
               net_connect.write_channel("quit\n" )
           _bkp_reader.close()
           print("")
           print("=========================================================================================================================")
           print("")
           time.sleep(2)

    report_file.close()
tseconds =round(timeit.default_timer() - start_geral)
m, s = divmod(tseconds, 60)
h, m = divmod(m, 60)
print ("")
print (f'Concluído em {h:d}:{m:02d}:{s:02d}')
if(device_cnt > 0):
    tseconds = tseconds / device_cnt
    m, s = divmod(tseconds, 60)
    h,  m = divmod(m, 60)
    print(f'Coletadas informações de {device_cnt:2d} dispositivos. Média de {tseconds:2.1f} segundos para cada um')
