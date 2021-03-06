#!/usr/bin/python3
# -*- coding: utf-8 -*
# Autor: Ricardo Tavares 07/10/2019

# Original general idea was got from Mauro Lucio (mauro.lucio@oi.net.br)
#
# Author: Ricardo Tavares (jose.ricardo.tavares@huawei.com/curupas.gmail.com)
#
# Title: Verifica Rotas Estáticas Inválidas em Roteadores Cisco IOS (aka Verifica Rotas) v1.1
# Description: Python script to read Cisco configuration files and audit it searching for static invalid routes.
# Description: This script was developed with Brazilian Portuguese native speakers in mind.
#
# Verifica Rotas is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Verifica Rotas is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# If you don't have a copy of the GNU General Public License,
# it is available here <http://www.gnu.org/licenses/>.


# Parameter '--routers' file format - it is a simple csv with a header line:
# device_ip
# cisco_config_ios-01
# cisco_config_ios-02
# cisco_config_ios-..
# cisco_config_ios-nn

# Parameter '--limpar' causes the script to generate simple output to paste at the config level of a Cisco IOS router

# import modules

from ciscoconfparse import CiscoConfParse
from ciscoconfparse.ccp_util import IPv4Obj
from argparse import ArgumentParser
import ipaddress, json,re, csv, time, timeit
import MySQLdb

def AchaGW(new_route_cmds,parse):
  parse=CiscoConfParse(device_row['device_ip'])
  interface_cmds = parse.find_objects(r"^interface ")
  static_ip = re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3} \d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', 
                      new_route_cmds)

  static_gw = re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', 
                       new_route_cmds)
  if(len(static_gw)==3):
      static_gw2= static_gw[2]
  else:
      return 2
  result = dict()
  result['interfaces'] = dict()

  for interface_cmd in interface_cmds:

     IPv4_REGEX = r"ip\saddress\s(\S+\s+\S+)"

     for cmd in interface_cmd.re_search_children(IPv4_REGEX):
        ipv4_addr = interface_cmd.re_match_iter_typed(IPv4_REGEX, result_type=IPv4Obj)

        _ATM=((interface_cmd.text).replace("point-to-point",""))
        #intf_name = re.split(r'\s+', interface_cmd.text)[-1]
        intf_name = re.split(r'\s+', (_ATM).strip())[-1]
        result['interfaces'][intf_name] = dict()
        result["interfaces"][intf_name].update({
            "ipv4": {
               "address": ipv4_addr.ip.exploded,
               "netmask": ipv4_addr.netmask.exploded
            }
        })
  for x in result:
     for y in result[x]:
         tmp=ipaddress.ip_network(result[x][y]["ipv4"]["address"] + "/" + 
                       result[x][y]["ipv4"]["netmask"], strict=False)
         tmp2=ipaddress.ip_network(static_gw2+"/32")

         if(tmp2.overlaps(tmp)):
             return 1
  return 0

# main section

if __name__ == "__main__":
    parser = ArgumentParser(description='Arguments for running oneLiner.py', add_help=False)
    parser.add_argument('-r', '--routers', required=True, action='store', help='Lista de roteadores')
    parser.add_argument('-l', '--limpar', action='store_true', help='Gera o comando para remoção das rotas inválidas')
    parser.add_argument('-b', '--bgp', action='store_true', help='Suprimir Análise BGP')
    parser.add_argument('-s', '--rotas', action='store_true', help='Suprimir Análise Rotas Estáticas')
    parser.add_argument('-h', '--help', action='help', help='Analisa arquivos de configuração Cisco IOS procurando por rotas estáticas inválidas')
    args = parser.parse_args()

    start_geral = timeit.default_timer()
    _TotalGeral= 0
    _TotalGeralV= 0

    mydb = MySQLdb.connect(host='localhost', user='shaolin', passwd='oretrec', db='BGP_Oi')
    _isubnet,_inexthop=1,2

    _device_ctr = 0
    _BGP_NOK_ctr = 0
    _BGP_OK_ctr = 0
    TOperations=0
    with open(args.routers, "r") as file:
        reader = csv.DictReader(file)
        for device_row in reader:

           _device_ctr = _device_ctr+1

           parse=CiscoConfParse(device_row['device_ip'])

           interface_cmds = parse.find_objects(r"^interface ")
           route_cmds = parse.find_objects(r"^ip route \d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3} \d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
           IPv4_REGEX = ""
           result = dict()
           result['interfaces'] = dict()

           start_time = timeit.default_timer()
           for interface_cmd in interface_cmds:

                IPv4_REGEX = r"ip\saddress\s(\S+\s+\S+)"

                for cmd in interface_cmd.re_search_children(IPv4_REGEX):
                    ipv4_addr = interface_cmd.re_match_iter_typed(IPv4_REGEX, result_type=IPv4Obj)

                    #print((interface_cmd.text).replace("point-to-point",""))
                    _ATM=((interface_cmd.text).replace("point-to-point",""))
                    #intf_name = re.split(r'\s+', interface_cmd.text)[-1]
                    intf_name = re.split(r'\s+', (_ATM).strip())[-1]
                    #print("intf",intf_name)
                    result['interfaces'][intf_name] = dict()
                    result["interfaces"][intf_name].update({
                        "ipv4": {
                            "address": ipv4_addr.ip.exploded,
                            "netmask": ipv4_addr.netmask.exploded
                        }
                    })

           for x in result:
                if(args.limpar is False):
                    print("==================================================================================")
                    print ("Interfaces no roteador " + device_row['device_ip'])
                    print("==================================================================================")
                    for y in result[x]:
                        print (device_row['device_ip'] + ": interface ",
                               y,':',ipaddress.ip_interface(result[x][y]["ipv4"]["address"] + "/" + result[x][y]["ipv4"]["netmask"]))

           #print(json.dumps(result, indent=4))
           _TotalParcial=0
           _TotalParcialV=0
# BGP 
           if(args.bgp is False):
           
              print("")
              print ("Análise das rotas BGP (/24 e /29) Apontadas para o roteador " + device_row['device_ip'])
              print("==================================================================================")
              for x in result:
                 for y in result[x]:
                    tmp=result[x][y]["ipv4"]["address"]
                    tmp2=ipaddress.ip_network(result[x][y]["ipv4"]["address"] + "/" + result[x][y]["ipv4"]["netmask"], strict=False)
                    cursor = mydb.cursor()
                    _SELECT='SELECT id,subnet,nexthop FROM rotas_bgp WHERE nexthop= %(GW)s ORDER BY subnet' 
                    _PARAM={ 'GW': "'"+tmp+"'" }
                    cursor.execute(_SELECT,_PARAM) 
                    row=cursor.fetchone()
                    while row is not None:

                       _subnet = (row[_isubnet]).replace("'","")
                       _nexthop= (row[_inexthop]).replace("'","")
                       BGP=False
                       if(ipaddress.ip_network(_nexthop).overlaps(tmp2)):
                           BGP=True
                           OnlyLoopback=True
                           print(f'{device_row["device_ip"]:s} {str(ipaddress.ip_network(_subnet)):s} gateway {str(_nexthop):s}({y:s}) -  [BGP]')
                           row=cursor.fetchone()
                           ip_bgp=ipaddress.ip_network(_subnet).with_netmask
                           route_configure = parse.find_objects(r"^ip route " + ip_bgp.replace("/"," ") + ".*")
                           #print(route_configure)
                           for new_routes in route_configure:
                               TOperations+=1
                               BGP_Flag=AchaGW(new_routes.text,parse)
                               #print("    " + device_row["device_ip"] +  ":    RECURSÃO: " + new_routes.text + ("  OKAY" if AchaGW(new_routes.text,parse) else "  ERRO"))
                               if(BGP_Flag == 0):
                                   print("    " + device_row["device_ip"] +  ":    RECURSÃO: " + new_routes.text + ("  ERRO"))
                                   _BGP_NOK_ctr=_BGP_NOK_ctr + 1
                                   OnlyLoopback=False
                                   print("")
                               elif(BGP_Flag == 1):
                                   print("    " + device_row["device_ip"] +  ":    RECURSÃO: " + new_routes.text + ("  OKAY"))
                                   _BGP_OK_ctr=_BGP_OK_ctr + 1
                                   OnlyLoopback=False
                                   print("")

                           if(OnlyLoopback):
                              print("    " + device_row["device_ip"] +  ":    Somente a interface Loopback foi encontrada como nexthop  ERRO")
                              print("")
                              _BGP_NOK_ctr=_BGP_NOK_ctr + 1
                            
                           continue
                       if(BGP is not True):
                           print(f'{device_row["device_ip"]:s} {str(ipaddress.ip_network(_subnet)):s} gateway {str(_nexthop):s}({y:s}) -  [BGP ERRO - CONFERIR]')
                           row=cursor.fetchone()

                    cursor.close()


           if(args.rotas is False):

              print("")
              print("==================================================================================")
              print ("Rotas estáticas no roteador " + device_row['device_ip'])
              print("==================================================================================")

              start_parcial = timeit.default_timer()
              for route_cmd in route_cmds:

                   static_ip = re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3} \d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', 
                                         route_cmd.text).group().replace(" ","/")

                   static_gw = re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', 
                                          route_cmd.text)
                   if(len(static_gw)==3):
                       static_gw2= static_gw[2]
                   else:
                       continue

                   _GW_FOUND=False
                   for x in result:
                      for y in result[x]:
                           tmp=ipaddress.ip_network(result[x][y]["ipv4"]["address"] + "/" + 
                                   result[x][y]["ipv4"]["netmask"], strict=False)
                           tmp2=ipaddress.ip_network(static_gw2+"/32")

                           if(tmp2.overlaps(tmp)):
                               if(args.limpar is False):
                                   print(device_row['device_ip'] +": "+ 
                                         str(ipaddress.ip_network(static_ip)) , " gateway "  , static_gw2 , "  -  [GW_FOUND]")

                               _TotalParcialV=_TotalParcialV + 1
                               _TotalGeralV=_TotalGeralV + 1
                               _GW_FOUND=True
                               break
                      if(_GW_FOUND):
                          break

                   if(not _GW_FOUND):
                       if(args.limpar is False):
                           print(device_row['device_ip'] + ": "+
                                 str(ipaddress.ip_network(static_ip)) , " gateway "  , static_gw2 , "  -  [GW_NOT_FOUND]")
                       else:
                           print(device_row['device_ip'] + ": " + "no ip route " +  static_ip.replace("/"," ") + "  " + static_gw2)
                       _TotalParcial=_TotalParcial + 1

                   _TotalGeral=_TotalGeral + 1


              print ("")
              print("==================================================================================")
              print (f'Total Parcial de Rotas Estáticas Válidas:{_TotalParcialV:3d}')
              print (f'Total Parcial de Rotas Estáticas Inválidas:{_TotalParcial:3d}')
              print ("")
              if(_TotalParcialV + _TotalParcial > 0):
                 print (f'Percentual Parcial de Rotas Inválidas { (_TotalParcial * 100) / (_TotalParcialV + _TotalParcial):.2f}%')
                 print ("")
              tseconds =round(timeit.default_timer() - start_geral)
              m, s = divmod(tseconds, 60)
              h, m = divmod(m, 60)
              print (f'Concluído em {h:d}:{m:02d}:{s:02d}')


    tseconds =round(timeit.default_timer() - start_geral)
    m, s = divmod(tseconds, 60)
    h, m = divmod(m, 60)

    print ("")
    print("==================================================================================")
    print (f'Total de Dispositivos Analisados:{_device_ctr:3d}')
    print ("")
    if(args.rotas is False):
       print (f'Total Geral de Rotas Estáticas Válidas:{_TotalGeralV:3d}')
       print (f'Total Geral de Rotas Estáticas Inválidas:{_TotalGeral:3d}')
       print("")
    if(args.bgp is False):
       print (f'Total Geral de Rotas BGP Válidas:{_BGP_OK_ctr:3d}')
       print (f'Total Geral de Rotas BGP Inválidas:{_BGP_NOK_ctr:3d}')
       print ("")
    print (f'Total Geral de Operações:{TOperations:4d}')
    print ("")
    if(args.rotas is False):
       print (f'Percentual Total de Rotas Inválidas { (_TotalGeral * 100) / (_TotalGeralV + _TotalGeral):.2f}%')
    if(args.bgp is False):
       print (f'Percentual Total de Rotas BGP Inválidas { (_BGP_NOK_ctr * 100) / (_BGP_OK_ctr + _BGP_NOK_ctr):.2f}%')
    print ("")
    print (f'Concluído em {h:d}:{m:02d}:{s:02d}')
    print ("")
