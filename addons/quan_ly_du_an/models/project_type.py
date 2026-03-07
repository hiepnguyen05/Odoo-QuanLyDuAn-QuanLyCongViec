# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ProjectType(models.Model):
    _name = 'project.type'
    _description = 'Loại dự án (VD: Web, BĐS)'

    name = fields.Char(string='Tên Loại Dự Án', required=True)
    task_template_ids = fields.One2many(
        'project.task.template', 
        'project_type_id', 
        string='Danh sách Công việc Mẫu'
    )
    
class ProjectTaskTemplate(models.Model):
    _name = 'project.task.template'
    _description = 'Công việc Mẫu tự động sinh'
    _order = 'sequence, id'

    name = fields.Char(string='Tên công việc', required=True)
    sequence = fields.Integer(string='Thứ tự', default=10)
    description = fields.Html(string='Mô tả công việc')
    
    project_type_id = fields.Many2one(
        'project.type', 
        string='Thuộc Loại Dự án', 
        required=True, 
        ondelete='cascade'
    )
