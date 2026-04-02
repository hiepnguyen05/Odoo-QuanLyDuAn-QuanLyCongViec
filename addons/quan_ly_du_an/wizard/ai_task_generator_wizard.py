# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AITaskGeneratorWizard(models.TransientModel):
    _name = 'ai.task.generator.wizard'
    _description = 'Wizard Review Công Việc do AI Gợi ý'

    project_id = fields.Many2one('project.project', string='Dự án', required=True)
    thanh_vien_ids = fields.Many2many(related='project_id.thanh_vien_ids')
    line_ids = fields.One2many(
        'ai.task.generator.line', 
        'wizard_id', 
        string='Danh sách Công việc Gợi ý'
    )

    def action_confirm_create(self):
        self.ensure_one()
        task_env = self.env['project.task']
        stage_env = self.env['project.task.type']
        # Tìm stage "Mới" của dự án này
        todo_stage = stage_env.search([
            ('project_ids', 'in', self.project_id.id),
            ('name', '=ilike', 'Mới')
        ], limit=1)
        
        # Nếu không thấy (hiếm khi xảy ra do logic create dự án mới), lấy đại 1 stage đầu tiên
        if not todo_stage:
            todo_stage = self.project_id.type_ids[0] if self.project_id.type_ids else False

        for line in self.line_ids:
            if not line.is_selected:
                continue
            new_task = task_env.create({
                'name': line.name,
                'description': line.description,
                'ai_sop': line.ai_sop,
                'project_id': self.project_id.id,
                'stage_id': todo_stage.id,
                'nhan_vien_ids': [(6, 0, line.nhan_vien_ids.ids)] if line.nhan_vien_ids else False,
            })
            if line.checklist_raw:
                checklist_names = [c.strip() for c in line.checklist_raw.split(',') if c.strip()]
                for idx, c_name in enumerate(checklist_names):
                    self.env['project.task.checklist'].create({
                        'name': c_name,
                        'task_id': new_task.id,
                        'sequence': (idx + 1) * 10
                    })
        
        return {'type': 'ir.actions.act_window_close'}

class AITaskGeneratorLine(models.TransientModel):
    _name = 'ai.task.generator.line'
    _description = 'Chi tiết Dòng Công việc AI'

    wizard_id = fields.Many2one('ai.task.generator.wizard', required=True, ondelete='cascade')
    is_selected = fields.Boolean(string='Chọn', default=True)
    name = fields.Char(string='Tên Công việc', required=True)
    description = fields.Text(string='Mô tả chi tiết')
    nhan_vien_ids = fields.Many2many('hr.employee', string='Người thực hiện') 
    ai_sop = fields.Html(string='Quy trình AI gợi ý')
    checklist_raw = fields.Text(string='Danh sách kiểm tra (txt)')
