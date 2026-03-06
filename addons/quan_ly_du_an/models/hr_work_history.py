# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class HrWorkHistory(models.Model):
    _name = 'hr.work.history'
    _description = 'Quá trình công tác nhân viên'
    _order = 'date_start desc'

    company_name = fields.Char(string='Tên công ty/Tổ chức', required=True)
    position = fields.Char(string='Chức vụ', required=True)
    date_start = fields.Date(string='Ngày bắt đầu', required=True)
    date_end = fields.Date(string='Ngày kết thúc')
    
    employee_id = fields.Many2one('hr.employee', string='Nhân viên', required=True, ondelete='cascade')

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for record in self:
            if record.date_start and record.date_end and record.date_end < record.date_start:
                raise ValidationError("Ngày kết thúc không được nhỏ hơn ngày bắt đầu!")
