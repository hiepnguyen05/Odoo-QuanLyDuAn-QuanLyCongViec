# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date

class HrFamily(models.Model):
    _name = 'hr.family'
    _description = 'Thông tin Thân nhân nhân viên'

    name = fields.Char(string='Họ và tên', required=True)
    relationship = fields.Selection([
        ('vo_chong', 'Vợ/Chồng'),
        ('con_de', 'Con đẻ'),
        ('con_nuoi', 'Con nuôi'),
        ('bo_me', 'Bố/Mẹ'),
        ('khac', 'Khác')
    ], string='Mối quan hệ', required=True)
    birth_date = fields.Date(string='Ngày sinh', required=True)
    is_dependent = fields.Boolean(
        string='Người phụ thuộc', 
        compute='_compute_is_dependent', 
        store=True, 
        readonly=False,
        help='Tự động đánh dấu là người phụ thuộc nếu là con (đẻ/nuôi) dưới 18 tuổi.'
    )
    
    employee_id = fields.Many2one('hr.employee', string='Nhân viên', required=True, ondelete='cascade')

    @api.depends('birth_date', 'relationship')
    def _compute_is_dependent(self):
        today = date.today()
        for record in self:
            if record.birth_date:
                age = today.year - record.birth_date.year
                if today.month < record.birth_date.month or \
                   (today.month == record.birth_date.month and today.day < record.birth_date.day):
                    age -= 1
                
                if record.relationship in ['con_de', 'con_nuoi'] and age < 18:
                    record.is_dependent = True
                else:
                    record.is_dependent = False
            else:
                record.is_dependent = False

    @api.constrains('birth_date', 'relationship')
    def _check_birth_date(self):
        today = date.today()
        for record in self:
            if record.birth_date and record.birth_date > today:
                raise ValidationError("Ngày sinh của thân nhân không được lớn hơn ngày hiện tại!")
                
            if record.employee_id and record.employee_id.birthday and record.birth_date:
                emp_birth = record.employee_id.birthday
                family_birth = record.birth_date
                
                # Bố/Mẹ phải sinh trước nhân viên (tối thiểu 15 năm)
                if record.relationship == 'bo_me':
                    if family_birth >= emp_birth:
                        raise ValidationError("Ngày sinh của Bố/Mẹ không được lớn/bằng ngày sinh của nhân viên!")
                    
                    age_diff = (emp_birth - family_birth).days / 365.25
                    if age_diff < 15:
                        raise ValidationError(f"Bố/Mẹ phải sinh trước nhân viên tối thiểu 15 năm (hiện tại cách {age_diff:.1f} năm)!")
                
                # Con cái phải sinh sau nhân viên (tối thiểu 15 năm)
                elif record.relationship in ['con_de', 'con_nuoi']:
                    if family_birth <= emp_birth:
                        raise ValidationError("Ngày sinh của Con phải lớn hơn ngày sinh của nhân viên!")
                        
                    age_diff = (family_birth - emp_birth).days / 365.25
                    if age_diff < 15:
                        raise ValidationError(f"Nhân viên phải sinh trước con tối thiểu 15 năm (hiện tại cách {age_diff:.1f} năm)!")
