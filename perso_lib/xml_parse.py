#!/usr/bin/python
# -*- coding: UTF-8 -*-
 
from xml.dom.minidom import parse
import xml.dom.minidom
 
class XmlParser:
    def __init__(self,file_name):
        self.file_name = file_name
        self.__dom = xml.dom.minidom.parse(file_name)
        self.__root_element = self.__dom.documentElement

    @property
    def root_element(self):
        return self.__root_element
    
    def get_nodes(self,parent_node,node_name):
        return parent_node.getElementsByTagName(node_name)

    def get_first_node(self,parent_node,node_name):
        nodes = self.get_nodes(parent_node,node_name)
        for node in nodes:
            return node
    
    def get_attribute(self,node,attr_name):
        if node.hasAttribute(attr_name):
            return node.getAttribute(attr_name)


if __name__ == '__main__':
    xml_parse = XmlParser('install.xml')
    nodes = xml_parse.get_nodes(xml_parse.root_element,'App')
    node = xml_parse.get_first_node(xml_parse.root_element,'App')
    attr = xml_parse.get_attribute(node,'type')
    xml_parse.get_nodes(xml_parse.root_element,"Encrypt")