# -*- coding: utf-8 -*-
from odoo import models, fields

class ProjectTaskChecklist(models.Model):
    _name = 'project.task.checklist'
    _description = 'Project Task Checklist'
    _order = 'sequence, id'

    name = fields.Char(string='Nội dung kiểm tra', required=True)
    is_done = fields.Boolean(string='Đã xong', default=False)
    sequence = fields.Integer(string='Thứ tự', default=10)
    task_id = fields.Many2one('project.task', string='Công việc', ondelete='cascade')
