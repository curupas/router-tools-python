#!/usr/bin/env python3.7
# Author: Ricardo Tavares (jose.ricardo.tavares@huawei.com/curupas.gmail.com)
#
# Title: Decode Huawei BGP Update Message

# This script is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This script is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# If you don't have a copy of the GNU General Public License,
# it is available here <http://www.gnu.org/licenses/>.


import binascii
from scapy.utils import *
from scapy.layers.inet import IP, TCP
from scapy.contrib.bgp import BGPHeader, BGPUpdate, BGPPathAttr, BGPNLRI_IPv4, BGPPALocalPref

"""
EXEMPLO DO FORMATO DO PACOTE DE ENTRADA (BGP UPDATE - MESSAGE COMPLETA) FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF0084020000006D4001010240020602010000FE078004040000000040050400000064C0100800021E3A00003155800904647A021E800A0C0000032A000000D200000136900E002D0001800C0000000000000000647A021E00603F86A100001E3A000032497F703F86A100001E3A000032490A523D
"""

banner= r"""

====================================================================================
Decodifica uma BGP UPDATE MESSAGE obtida através do commando "debug bgp raw-packet"

Autor: Ricardo Tavares (jose.ricardo.tavares@huawei.com) - 29/Jan/2020

Requer Scapy 2.4 - Válido para dispositivos Huawei rodando VRP8
====================================================================================

"""

print(banner)

bgp_packet_dbg = input("Pacote Capturado com 'debug bgp raw-packet': ")
file_pcap_name = input("Nome do Arquivo .CAP (WireShark) [output.cap]: ") or "output.cap"

src_ipv4_addr = input("Source IP [10.10.10.1]: ") or '10.10.10.1'
dst_ipv4_addr = input("Destination IP [10.10.10.100]: ") or '10.10.10.100'

established_port= 1311
expected_seq_num=1000
current_seq_num=1500

base = IP(src=src_ipv4_addr, dst=dst_ipv4_addr, proto=6, ttl=255)
tcp = TCP(sport=established_port, dport=179, seq=current_seq_num, ack=expected_seq_num, flags=['PA']) 
hdr = raw(binascii.unhexlify(bgp_packet_dbg.replace(' ','')))
packet = base / tcp / hdr 

# Exibe o decoding na tela (remova o comentário)
#packet.show2()

# Grava o decoding no formato .CAP (para ser carregado no Wireshark) 
wrpcap(file_pcap_name, packet)
