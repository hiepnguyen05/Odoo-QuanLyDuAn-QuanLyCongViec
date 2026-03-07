# -*- coding: utf-8 -*-
"""
Kế thừa và mở rộng project.project
Thêm quản lý thành viên dự án và tính tiến độ
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import requests
import json
import re


class ProjectProject(models.Model):
    """Kế thừa project.project để thêm quản lý thành viên"""
    _inherit = 'project.project'
    
    # ==================== FIELDS ====================
    
    # ==================== CHO TÍNH NĂNG MỨC 2: AUTOMATION ====================
    project_type_id = fields.Many2one(
        'project.type', 
        string='Loại Dự án (Tự động hóa)', 
        help="Chọn Loại Dự án để hệ thống Sinh Tự Động các Công việc đặc thù mẫu."
    )
    
    @api.model
    def create(self, vals):
        # 1. Gọi hàm Create gốc của Odoo để hệ thống lưu Dự án này vào Database trước
        project = super(ProjectProject, self).create(vals)
        
        # 2. Logic Automation Mức 2: Nếu Dự án có gắn "Loại", tiến hành Auto-Generate Tasks
        if project.project_type_id and project.project_type_id.task_template_ids:
            task_env = self.env['project.task']
            # Duyệt qua từng công việc mẫu của Loại này
            for template in project.project_type_id.task_template_ids:
                # Đẻ ra các công việc con (Task) và map project_id về đúng Dự án mới
                task_env.create({
                    'name': template.name,
                    'description': template.description,
                    'project_id': project.id,
                    'sequence': template.sequence,
                })
        
        return project    
    thanh_vien_ids = fields.Many2many(
        comodel_name='hr.employee',
        relation='project_employee_rel',
        column1='project_id',
        column2='employee_id',
        string='Thành viên dự án',
        help='Danh sách nhân viên được phép tham gia dự án này'
    )
    
    so_luong_thanh_vien = fields.Integer(
        string='Số lượng thành viên',
        compute='_compute_so_luong_thanh_vien',
        store=True,
        help='Tổng số thành viên trong dự án'
    )
    
    progress = fields.Float(
        string='Tiến độ (%)',
        compute='_compute_progress',
        store=False,
        help='Tiến độ được tính tự động từ % hoàn thành của các task'
    )
    
    # Field Tính tổng số Lượng Task (Cả Task tự tay đẻ + Task auto sinh)
    so_luong_task = fields.Integer(
        string='Số Công việc', 
        compute='_compute_so_luong_task'
    )

    # ==================== COMPUTED METHODS ====================
    
    @api.depends('thanh_vien_ids')
    def _compute_so_luong_thanh_vien(self):
        """Tính số lượng thành viên trong dự án"""
        for record in self:
            record.so_luong_thanh_vien = len(record.thanh_vien_ids)
    
    @api.depends('task_ids', 'task_ids.stage_id')
    def _compute_progress(self):
        """
        Tính % tiến độ dự án dựa trên số task hoàn thành (real-time)
        Công thức: (Số task Done / Tổng số task) * 100
        Nhận diện Hoàn thành qua is_closed, fold hoặc theo tên (Đã giao, Xong, Hoàn thành).
        """
        for project in self:
            tasks = project.task_ids
            if tasks:
                completed_tasks = tasks.filtered(
                    lambda t: t.stage_id and (
                        t.stage_id.fold or 
                        getattr(t.stage_id, 'is_closed', False) or 
                        any(keyword in t.stage_id.name.lower() for keyword in ['xong', 'giao', 'hoàn thành', 'done'])
                    )
                )
                project.progress = (len(completed_tasks) / len(tasks)) * 100
            else:
                project.progress = 0.0
    
    def _compute_so_luong_task(self):
        for record in self:
            record.so_luong_task = self.env['project.task'].search_count([
                ('project_id', '=', record.id)
            ])
            
    # ==================== ACTION METHODS ====================
    
    def action_view_tasks(self):
        self.ensure_one()
        return {
            'name': 'Công việc liên quan',
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'view_mode': 'kanban,tree,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }

    # ==================== CHO TÍNH NĂNG MỨC 1 ====================        
    def action_view_team_members(self):
        """Smart button để xem danh sách thành viên dự án"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Thành viên dự án',
            'res_model': 'hr.employee',
            'view_mode': 'tree,form,kanban',
            'domain': [('id', 'in', self.thanh_vien_ids.ids)],
            'target': 'current',
        }
    
    # ==================== CONSTRAINTS ====================
    
    @api.constrains('thanh_vien_ids')
    def _check_thanh_vien_ids(self):
        """Kiểm tra phải có ít nhất 1 thành viên trong dự án"""
        for record in self:
            if record.thanh_vien_ids and len(record.thanh_vien_ids) == 0:
                raise ValidationError(
                    "❌ Dự án phải có ít nhất 1 thành viên!"
                )

    # ==================== TÍCH HỢP AI GEMINI MỨC 3 ====================
    def action_generate_tasks_ai(self):
        """
        Gọi API Gemini để phân tích tên/mô tả dự án và tự động tạo Task.
        """
        self.ensure_one()
        
        if not self.name:
            raise UserError(_("Vui lòng nhập Tên Dự án trước khi dùng AI gợi ý công việc."))
            
        # Cẩn thận: Lấy API Key từ Cấu hình hệ thống (Database) thay vì code cứng
        api_key = self.env['ir.config_parameter'].sudo().get_param('gemini.api_key')
        
        if not api_key:
            raise UserError(_("Chưa cấu hình API Key cho Gemini AI. \n"
                              "Vui lòng vào 'Thiết lập' -> 'Kỹ thuật' -> 'Thông số hệ thống' \n"
                              "và tạo mới thông số có Khóa (Key) là 'gemini.api_key' rồi dán API key của bạn vào Giá trị (Value)."))
                              
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        
        # Tạo Prompt gửi cho Gemini
        prompt = f"""
        Tôi đang quản lý một dự án có tên là: "{self.name}".
        Hãy đóng vai là một chuyên gia quản lý dự án, phân tích và gợi ý cho tôi danh sách từ 5 đến 7 công việc chi tiết cần thực hiện cho dự án này.
        
        Về Tên Cột Kanban (stage_name), hãy xem xét phân loại các công việc dựa trên một trong các Mẫu (Template) Kanban tiêu chuẩn sau đây nếu phù hợp với ngữ cảnh:
        1. Phát triển phần mềm: Chưa thực hiện, Đặc điểm, Phát triển, Chạy thử, Đã giao
        2. Agile Scrum: Backlog, Trực Nhật, Đang thực hiện, Hoàn thành
        3. Tiếp thị số: Ý tưởng, Đang lên kế hoạch, Đang chạy, Đã xong
        4. Thiết kế: Yêu cầu, Lên ý tưởng, Thiết kế sơ bộ, Chờ duyệt, Hoàn thiện
        5. Cơ bản: Cần làm, Đang làm, Hoàn thành
        Nếu dự án mang tính chất đặc thù khác, bạn có thể tự đưa ra các tên Cột Kanban hợp lý nhất.
        
        Trả lời BẮT BUỘC chỉ bằng một Object JSON nguyên chất, định dạng chính xác phân tích cú pháp được, với cấu trúc như sau:
        {{
            "kanban_stages": "Việc cần làm, Phân tích, Lập trình, Chạy thử, Đã hoàn thành",
            "tasks": [
                {{"name": "Tên công việc 1", "description": "Mô tả chi tiết công việc 1"}},
                {{"name": "Tên công việc 2", "description": "Mô tả chi tiết công việc 2"}}
            ]
        }}
        Lưu ý: "kanban_stages" là chuỗi các tên cột cách nhau bởi dấu phẩy, dựa theo loại dự án.
        Không có thêm bất kỳ văn bản nào khác ngoài Object JSON này.
        """
        
        headers = {'Content-Type': 'application/json'}
        data = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        
        try:
            # Gửi Request
            response = requests.post(url, headers=headers, data=json.dumps(data), timeout=30)
            
            if response.status_code == 200:
                result_json = response.json()
                
                # Bóc tách câu trả lời của AI
                if 'candidates' in result_json and len(result_json['candidates']) > 0:
                    text_response = result_json['candidates'][0]['content']['parts'][0]['text']
                    
                    # Cố gắng dọn dẹp markdown code block
                    cleaned_text = re.sub(r'```json\n|```', '', text_response).strip()
                    
                    try:
                        # Parse JSON thành dictionary
                        result_dict = json.loads(cleaned_text)
                        
                        tasks_data = result_dict.get('tasks', [])
                        kanban_stages_str = result_dict.get('kanban_stages', '')
                        
                        # Thay vì tạo Task ngay, Ta tạo Data cho Wizard
                        wizard_lines = []
                        for task_dict in tasks_data:
                            task_name = task_dict.get('name')
                            if task_name:
                                wizard_lines.append((0, 0, {
                                    'name': task_name,
                                    'description': task_dict.get('description', ''),
                                }))
                                
                        if wizard_lines or kanban_stages_str:
                            # Tạo bản ghi Wizard trong RAM
                            wizard = self.env['ai.task.generator.wizard'].create({
                                'project_id': self.id,
                                'suggested_kanban_stages': kanban_stages_str,
                                'line_ids': wizard_lines
                            })
                            
                            # Trả về Action mở Popup Wizard để User sửa
                            return {
                                'name': _('🤖 Check & Edit Gợi ý Của AI'),
                                'type': 'ir.actions.act_window',
                                'res_model': 'ai.task.generator.wizard',
                                'res_id': wizard.id,
                                'view_mode': 'form',
                                'target': 'new', # Mở Popup
                            }
                        else:
                            raise UserError(_("AI trả về kết quả nhưng không có công việc nào hợp lệ được tìm thấy."))
                            
                    except json.JSONDecodeError:
                        raise UserError(_(f"Không thể phân tích dữ liệu AI trả về do sai định dạng JSON.\nDữ liệu thô AI trả về:\n{text_response}"))
                        
                else:
                    raise UserError(_("Gemini API không có câu trả lời (candidates list rỗng)."))
                    
            else:
                raise UserError(_(f"Lỗi khi gọi API Gemini.\nMã lỗi: {response.status_code}\nChi tiết: {response.text}"))
                
        except requests.exceptions.Timeout:
            raise UserError(_("Kết nối tới Gemini API bị quá hạn (Timeout). Vui lòng thử lại sau."))
        except requests.exceptions.ConnectionError:
            raise UserError(_("Không thể kết nối đến Gemini API. Vui lòng kiểm tra lại mạng."))
        except Exception as e:
            raise UserError(_(f"Có lỗi bất ngờ xảy ra khi dùng AI:\n{str(e)}"))
