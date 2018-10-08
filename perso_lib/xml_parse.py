#!/usr/bin/python
# -*- coding: UTF-8 -*-
 
from xml.dom.minidom import parse
from xml.dom import minidom
from enum import Enum

class XmlMode(Enum):
    READ = 1
    WRITE = 2
    READ_WRITE = 4

class XmlParser:
    def __init__(self,file_name, mode=XmlMode.READ):
        self.file_name = file_name
        if mode == XmlMode.WRITE:
            self.__dom = None
            self.__root_element = None
        else:
            self.__dom = minidom.parse(file_name)
            self.__root_element = self.__dom.documentElement

    @property
    def root_element(self):
        return self.__root_element

    def create_root_element(self,root_name,**attr):
        self.__dom = minidom.Document()
        self.__root_element = self.__dom.createElement(root_name)
        self.__dom.appendChild(self.__root_element)
        for _,value in attr.items():
            self.__root_element.setAttribute(value[0],value[1])
        return self.__root_element

    def add_node(self,parent_node,node_name,**attr):
        new_node = self.__dom.createElement(node_name)
        for _,value in attr.items():
            new_node.setAttribute(value[0],value[1])
        parent_node.appendChild(new_node)
        return new_node

    def add_text(self,node,text):
        text_node = self.__dom.createTextNode(text)
        node.appendChild(text_node)

    # def writexml(self, writer, indent="", addindent="", newl=""):
    #     # indent = current indentation
    #     # addindent = indentation to add to higher levels
    #     # newl = newline string
    #     writer.write(indent+"<" + self.tagName)

    #     attrs = self._get_attributes()
    #     a_names = sorted(attrs.keys())

    #     for a_name in a_names:
    #         writer.write(" %s=\"" % a_name)
    #         _write_data(writer, attrs[a_name].value)
    #         writer.write("\"")
    #     if self.childNodes:
    #         writer.write(">")
    #         if (len(self.childNodes) == 1 and
    #             self.childNodes[0].nodeType == Node.TEXT_NODE):
    #             self.childNodes[0].writexml(writer, '', '', '')
    #         else:
    #             writer.write(newl)
    #             for node in self.childNodes:
    #                 node.writexml(writer, indent+addindent, addindent, newl)
    #             writer.write(indent)
    #         writer.write("</%s>%s" % (self.tagName, newl))
    #     else:
    #         writer.write("/>%s"%(newl))

    def save(self,char_type='GB2312'):
        try:
            with open(self.file_name,'w',encoding=char_type) as fh:
                self.__dom.writexml(fh,indent='',addindent='\t',newl='\n',encoding=char_type)
        except Exception as err:
            print('xml保存失败：{0}'.format(err))
          
    def get_nodes(self,parent_node,node_name):
        return parent_node.getElementsByTagName(node_name)

    def get_first_node(self,parent_node,node_name):
        nodes = self.get_nodes(parent_node,node_name)
        for node in nodes:
            return node
    
    def get_attribute(self,node,attr_name):
        if node.hasAttribute(attr_name):
            return node.getAttribute(attr_name)

    def get_attributes(self,node):
        dict_attr = {}
        for key in node.attributes.keys():
            attr = node.attributes[key]
            dict_attr[attr.name] = attr.value
        return dict_attr


if __name__ == '__main__':
    xml_parse = XmlParser('install.xml')
    nodes = xml_parse.get_nodes(xml_parse.root_element,'App')
    node = xml_parse.get_first_node(xml_parse.root_element,'App')
    attr = xml_parse.get_attribute(node,'type')
    xml_parse.get_nodes(xml_parse.root_element,"Encrypt")