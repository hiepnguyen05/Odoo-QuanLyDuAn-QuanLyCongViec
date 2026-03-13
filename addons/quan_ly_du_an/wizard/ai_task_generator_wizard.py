# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AITaskGeneratorWizard(models.TransientModel):
    _name = 'ai.task.generator.wizard'
    _description = 'Wizard Review Công Việc do AI Gợi ý'

    project_id = fields.Many2one('project.project', string='Dự án', required=True)
    thanh_vien_ids = fields.Many2many(related='project_id.thanh_vien_ids')
    suggested_kanban_stages = fields.Char(string='Gợi ý các Cột Kanban', help='Các cột Kanban do AI đề xuất, cách nhau bằng dấu phẩy')
    line_ids = fields.One2many(
        'ai.task.generator.line', 
        'wizard_id', 
        string='Danh sách Công việc Gợi ý'
    )

    def action_confirm_create(self):
        """Hàm này chạy khi người dùng ấn nút 'Xác nhận Sinh Công việc'"""
        self.ensure_one()
        task_env = self.env['project.task']
        stage_env = self.env['project.task.type']
        
        # Tạo mapping để hạn chế Query Cột Kanban nhiều lần
        stage_map = {}
        
        # Biến đếm thứ tự cột để ép Odoo sắp xếp đúng vị trí
        sequence_counter = 10
        
        # [Bước 1] Luôn luôn tạo hoặc lấy cột "Việc cần làm" làm cột gốc
        todo_stage = stage_env.search([
            ('project_ids', 'in', self.project_id.id),
            ('name', '=ilike', '%cần làm%')
        ], limit=1)
        
        if not todo_stage:
            todo_stage = stage_env.create({
                'name': 'Việc cần làm',
                'project_ids': [(4, self.project_id.id)],
                'sequence': 1
            })
            
        stage_map[todo_stage.name] = todo_stage

        # [Bước 2] Lặp qua các Cột Kanban do AI gợi ý (chứa trong chuỗi suggested_kanban_stages)
        if self.suggested_kanban_stages:
            stage_names = [s.strip() for s in self.suggested_kanban_stages.split(',') if s.strip()]
            for stage_name_clean in stage_names:
                if stage_name_clean in stage_map:
                    continue
                    
                # Phân tích keyword để xem có phải cột "Hoàn thành" không
                is_closed = False
                fold = False
                lower_name = stage_name_clean.lower()
                if any(k in lower_name for k in ['xong', 'hoàn thành', 'done', 'giao', 'hoàn thiện']):
                    is_closed = True
                    fold = True

                # Kế thừa bỏ qua việc tạo trùng tên với cột Cần làm đã tạo ở trên
                if any(k in lower_name for k in ['cần làm', 'yêu cầu', 'todo', 'backlog']):
                    continue

                # Tìm xem project này đã có cột stage tên này chưa
                existing_stage = stage_env.search([
                    ('name', '=ilike', stage_name_clean),
                    ('project_ids', 'in', self.project_id.id)
                ], limit=1)
                
                if not existing_stage:
                    # Nếu chưa có thì tự động tạo Cột Kanban mới, và map Project vào Cột đó
                    new_stage = stage_env.create({
                        'name': stage_name_clean,
                        'project_ids': [(4, self.project_id.id)],
                        'is_closed': is_closed,
                        'fold': fold,
                        'sequence': sequence_counter
                    })
                    stage_map[stage_name_clean] = new_stage
                else:
                    stage_map[stage_name_clean] = existing_stage
                    
                sequence_counter += 10

        # [Bước 3] Lặp qua các dòng gợi ý Công việc (Task) của AI
        for line in self.line_ids:
            if not line.is_selected:
                continue

            # Tạo Task và nhét tất cả vào Cột "Việc cần làm" (todo_stage)
            new_task = task_env.create({
                'name': line.name,
                'description': line.description,
                'ai_sop': line.ai_sop,
                'project_id': self.project_id.id,
                'stage_id': todo_stage.id,
                'nhan_vien_ids': [(6, 0, line.nhan_vien_ids.ids)] if line.nhan_vien_ids else False,
            })
            
            # Tạo Checklist từ chuỗi raw của AI (phân tách bởi dấu phẩy)
            if line.checklist_raw:
                checklist_names = [c.strip() for c in line.checklist_raw.split(',') if c.strip()]
                for idx, c_name in enumerate(checklist_names):
                    self.env['project.task.checklist'].create({
                        'name': c_name,
                        'task_id': new_task.id,
                        'sequence': (idx + 1) * 10
                    })
            
        # [Bước 4] Check xem Project đã có ít nhất 1 cột "Hoàn thành" để User kéo thẻ chưa
        has_done_stage = stage_env.search([
            ('project_ids', 'in', self.project_id.id),
            '|', ('is_closed', '=', True), 
                 ('name', '=ilike', '%Hoàn thành%')
        ], limit=1)
        
        if not has_done_stage:
            # Tự động tạo thêm cột Đã hoàn thành nếu AI không gợi ý
            stage_env.create({
                'name': 'Đã hoàn thành',
                'project_ids': [(4, self.project_id.id)],
                'is_closed': True,
                'fold': True,
                'sequence': 100
            })
            
        return {'type': 'ir.actions.act_window_close'}


class AITaskGeneratorLine(models.TransientModel):
    _name = 'ai.task.generator.line'
    _description = 'Chi tiết Dòng Công việc AI'

    wizard_id = fields.Many2one('ai.task.generator.wizard', required=True, ondelete='cascade')
    is_selected = fields.Boolean(string='Chọn', default=True, help="Bỏ chọn nếu bạn không muốn tạo công việc này")
    name = fields.Char(string='Tên Công việc', required=True)
    description = fields.Text(string='Mô tả chi tiết')
    
    # Cho phép người dùng chọn nhân viên thực hiện (lọc theo thành viên dự án nếu cần)
    nhan_vien_ids = fields.Many2many('hr.employee', string='Người thực hiện') 
    
    ai_sop = fields.Html(string='Quy trình AI gợi ý')
    checklist_raw = fields.Text(string='Danh sách kiểm tra (txt)', help='Chuỗi text phân tách bởi dấu phẩy')
