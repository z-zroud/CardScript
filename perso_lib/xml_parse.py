#!/usr/bin/python
# -*- coding: UTF-8 -*-
 
from xml.dom.minidom import parse
from xml.dom import minidom
from xml.dom import Node
from enum import Enum

# ==由于minidom默认的writexml()函数在读取一个xml文件后，修改后重新写入如果加了newl='\n',
# 会将原有的xml中写入多余的行  
#　 ==因此使用下面这个函数来代替  
def fixed_writexml(self, writer, indent="", addindent="", newl=""):  
    # indent = current indentation
    # addindent = indentation to add to higher levels
    # newl = newline string
    writer.write(indent+"<" + self.tagName)  

    attrs = self._get_attributes()  
    a_names = attrs.keys()  
    # a_names.sort()  


    for a_name in a_names:  
        writer.write(" %s=\"" % a_name)  
        minidom._write_data(writer, attrs[a_name].value)  
        writer.write("\"")  
    if self.childNodes:  
        if len(self.childNodes) == 1 and self.childNodes[0].nodeType == minidom.Node.TEXT_NODE:  
            writer.write(">")  
            self.childNodes[0].writexml(writer, "", "", "")  
            writer.write("</%s>%s" % (self.tagName, newl))  
            return  
        writer.write(">%s"%(newl))  
        for node in self.childNodes:  
            if node.nodeType is not minidom.Node.TEXT_NODE:  
                node.writexml(writer,indent+addindent,addindent,newl)  
        writer.write("%s</%s>%s" % (indent,self.tagName,newl))  
    else:  
        writer.write("/>%s"%(newl))  

minidom.Element.writexml = fixed_writexml

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
        for key,value in attr.items():
            new_node.setAttribute(key,value)
        parent_node.appendChild(new_node)
        return new_node

    def create_node(self,node_name,**attr):
        new_node = self.__dom.createElement(node_name)
        for key,value in attr.items():
            new_node.setAttribute(key,value)
        return new_node

    def add_text(self,node,text):
        text_node = self.__dom.createTextNode(text)
        node.appendChild(text_node)

    def add_comment(self,parent_node,comment):
        comm_node = self.__dom.createComment(comment)
        parent_node.appendChild(comm_node)

    def save(self,char_type='GB2312'):
        try:
            with open(self.file_name,'w',encoding=char_type) as fh:
                self.__dom.writexml(fh,indent='',addindent='\t',newl='\n',encoding=char_type)
        except Exception as err:
            print('xml保存失败：{0}'.format(err))
          
    def get_nodes(self,parent_node,node_name):
        '''
        获取父节点下所有node_name指定名称的节点，包含迭代子节点
        '''
        return parent_node.getElementsByTagName(node_name)

    def insert_before(self,parent_node,new_node,before_node):
        parent_node.insertBefore(new_node,before_node)

    def remove_node(self,parent_node,node_name):
        node = self.get_first_node(parent_node,node_name)
        if node:
            parent_node.removeChild(node)

    def remove(self,node):
        parent_node = node.parentNode
        if parent_node:
            parent_node.removeChild(node)

    def get_parent(self,node):
        return node.parentNode

    def get_node_by_attribute(self,parent_node,node_name,**attr):
        child_nodes = self.get_nodes(parent_node,node_name)
        for node in child_nodes:
            found = True
            for key,value in attr.items():
                attr_value = self.get_attribute(node,key,'')
                if attr_value != value:
                    found = False
                    break
            if found:
                return node
        return None

    def get_child_nodes(self,parent_node,node_name=None):
        '''
        获取父节点直接子节点名称为node_name的子节点，如果node_name
        为None,则获取所有直接子节点
        '''
        child_nodes = []
        for child_node in parent_node.childNodes:
            if child_node.nodeType == Node.ELEMENT_NODE:
                if node_name:
                    if child_node.nodeName == node_name:
                        child_nodes.append(child_node)
                else:
                    child_nodes.append(child_node)
        return child_nodes           

    def get_first_node(self,parent_node,node_name):
        nodes = self.get_nodes(parent_node,node_name)
        for node in nodes:
            return node
        return []
    
    def get_attribute(self,node,attr_name,default=None):
        if node.hasAttribute(attr_name):
            return node.getAttribute(attr_name)

    def get_attributes(self,node):
        dict_attr = {}
        for key in node.attributes.keys():
            attr = node.attributes[key]
            dict_attr[attr.name] = attr.value
        return dict_attr

    def remove_attribute(self,node,name):
        if name in node.attributes:
            node.removeAttribute(name)

    def set_attribute(self,node,name,value):
        node.setAttribute(name,value)

    def get_text(self,node):
        if node:
            for child_node in node.childNodes:
                if child_node.nodeName == '#text':
                    return child_node.data
        return None



if __name__ == '__main__':
    xml_parse = XmlParser('D:\\xml_test.xml')
    book_node = xml_parse.get_first_node(xml_parse.root_element,'book')
    name_node = xml_parse.get_first_node(book_node,'name')
    value = xml_parse.get_text(name_node)
    exit(1)