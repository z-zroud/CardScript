import os
from docx import Document
from docx.shared import Inches
from docx.oxml.ns import nsdecls
from docx.oxml import parse_xml
class Docx:
    def __init__(self,doc_name):
        if doc_name:
            self.doc = Document(doc_name)
        else:
            self.doc = Document()
        self.doc_name = doc_name

    def add_heading(self,title_level,title):
        '''
        添加标题
        title_level 表示添加"标题xx"
        title 标题名称
        '''
        self.doc.add_heading(title, level=title_level)

    def add_paragraph(self,content):
        return self.doc.add_paragraph(content)

    def set_paragraph_property(self,paragraph,blod,font_size,font_color,bk_color):
        pass

    def add_table(self,row=1,col=1,style=None):
        return self.doc.add_table(rows=row,cols=col, style='Table Grid')

    def get_cell(self,table,row,col):
        return table.rows[row].cells[col]
    
    def set_cell_property(self,cell,bk_color=None):
        shading_elm_1 = parse_xml(r'<w:shd {0} w:fill="{1}"/>'.format(nsdecls('w'),bk_color))
        cell._tc.get_or_add_tcPr().append(shading_elm_1)

    def set_cell_text(self,cell,text):
        cell.text = text


    def close(self):
        self.doc.save(self.doc_name)
    
    def save_as(self,doc_name):
        self.doc.save(doc_name)


if __name__ == '__main__':
    cwd = os.path.dirname(os.path.abspath(__file__))
    doc_path = cwd + os.path.sep + 'DP开发需求.docx'
    document = Docx(doc_path)
    document.add_heading(2,'Visa 分组')
    document.add_heading(3,'DGI0101')
    new_table = document.add_table(3,4)
    for col in range(4):
        cell = document.get_cell(new_table,0,col)
        document.set_cell_property(cell,'FFCA00')
    for row in range(1,3):
        for col in range(4):
            cell = document.get_cell(new_table,row,col)
            document.set_cell_text(cell,'AA')
    new_row = new_table.add_row()
    for cell in new_row.cells:
        document.set_cell_text(cell,'BB')
    document.save_as('demo.docx')

    # document.add_heading('Document Title', 0)

    # p = document.add_paragraph('A plain paragraph having some ')
    # p.add_run('bold').bold = True
    # p.add_run(' and some ')
    # p.add_run('italic.').italic = True

    # # document.add_heading('Heading, level 1', level=1)
    # # document.add_paragraph('Intense quote', style='Intense Quote')

    # # document.add_paragraph(
    # #     'first item in unordered list', style='List Bullet'
    # # )
    # # document.add_paragraph(
    # #     'first item in ordered list', style='List Number'
    # # )

    # records = (
    #     (3, '101', 'Spam'),
    #     (7, '422', 'Eggs'),
    #     (4, '631', 'Spam, spam, eggs, and spam')
    # )

    # table = document.add_table(rows=1, cols=3)
    # table.style = 'Table Grid'
    # hdr_cells = table.rows[0].cells
    # hdr_cells[0].text = 'Qty'
    # hdr_cells[0].style = 'yellow'
    # hdr_cells[1].text = 'Id'
    # hdr_cells[2].text = 'Desc'
    # for qty, id, desc in records:
    #     row_cells = table.add_row().cells
    #     row_cells[0].text = str(qty)
    #     row_cells[0].style = 'yellow'
    #     row_cells[1].text = id
    #     row_cells[2].text = desc

    # document.add_page_break()





    # new_table = document.add_table(rows=1,cols=3, style='Table Grid')
    # shading_elm_1 = parse_xml(r'<w:shd {} w:fill="1F5C8B"/>'.format(nsdecls('w')))
    # new_table.rows[0].cells[0]._tc.get_or_add_tcPr().append(shading_elm_1)

    # document.save('demo.docx')