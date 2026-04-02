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
import time


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
        # 1. Gọi hàm Create gốc của Odoo
        project = super(ProjectProject, self).create(vals)
        
        # 2. Tự động gán và MỞ RỘNG 5 trạng thái CÔNG VIỆC (project.task.type)
        task_stage_xml_ids = [
            'quan_ly_du_an.project_stage_new',
            'quan_ly_du_an.project_stage_in_progress',
            'quan_ly_du_an.project_stage_paused',
            'quan_ly_du_an.project_stage_done',
            'quan_ly_du_an.project_stage_cancelled',
        ]
        standard_task_stages = self.env['project.task.type']
        for xml_id in task_stage_xml_ids:
            stage = self.env.ref(xml_id, raise_if_not_found=False)
            if stage:
                # Ép buộc mở rộng cột (Unfold) nếu đang bị đóng
                if stage.fold:
                    stage.sudo().write({'fold': False})
                standard_task_stages |= stage
                
        if standard_task_stages:
            # Sử dụng sudo() để tránh lỗi phân quyền khi gán trạng thái công việc
            project.sudo().write({'type_ids': [(6, 0, standard_task_stages.ids)]})

        # 3. Tự động gán và MỞ RỘNG trạng thái DỰ ÁN (project.project.stage)
        project_stage_xml_ids = [
            'quan_ly_du_an.project_project_stage_new',
            'quan_ly_du_an.project_project_stage_in_progress',
            'quan_ly_du_an.project_project_stage_paused',
            'quan_ly_du_an.project_project_stage_done',
            'quan_ly_du_an.project_project_stage_cancelled',
        ]
        
        # Đảm bảo tất cả Project Stages cũng được mở rộng
        for xml_id in project_stage_xml_ids:
            p_stage = self.env.ref(xml_id, raise_if_not_found=False)
            if p_stage and p_stage.fold:
                p_stage.sudo().write({'fold': False})

        if hasattr(project, 'stage_id'):
            first_project_stage = self.env.ref(project_stage_xml_ids[0], raise_if_not_found=False)
            if first_project_stage:
                # Sử dụng sudo() vì trường stage_id yêu cầu quyền Kỹ thuật
                project.sudo().stage_id = first_project_stage.id

        # 3. Logic Automation Mức 2: Nếu Dự án có gắn "Loại", tiến hành Auto-Generate Tasks
        if project.project_type_id and project.project_type_id.task_template_ids:
            task_env = self.env['project.task']
            for template in project.project_type_id.task_template_ids:
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
    
    @api.depends('tasks', 'tasks.stage_id')
    def _compute_progress(self):
        """
        Tính % tiến độ dự án dựa trên số task hoàn thành (real-time)
        Công thức: (Số task Done / Tổng số task) * 100
        Nhận diện Hoàn thành qua is_closed, fold hoặc theo tên (Đã giao, Xong, Hoàn thành).
        Sử dụng fields 'tasks' thay vì 'task_ids' để tránh bị lọc mất các task đã đóng.
        """
        for project in self:
            tasks = project.tasks
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
            
    # ==================== OVERRIDE METHODS ====================
    def write(self, vals):
        """Mở rộng hàm write để tự động chuyển trạng thái dự án (Mức 2)"""
        res = super(ProjectProject, self).write(vals)
        
        # Nếu đã hoàn thành 100% thì tự động nhảy Stage
        for project in self:
            if project.progress == 100.0:
                # Tìm stage có tên liên quan đến hoàn thành/xong
                done_stage = self.env['project.project.stage'].search([
                    '|', '|', '|',
                    ('name', 'ilike', 'xong'),
                    ('name', 'ilike', 'hoàn thành'),
                    ('name', 'ilike', 'đã giao'),
                    ('name', 'ilike', 'done')
                ], limit=1)
                if done_stage and project.stage_id != done_stage:
                    # Dùng sudo() để đảm bảo phân quyền
                    project.sudo().stage_id = done_stage.id
        return res

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
                              
        # Danh sách model thử lần lượt (từ mới nhất đến cũ nhất, đã loại bỏ gemini-pro bị Google ngừng hỗ trợ)
        model_candidates = [
            'gemini-2.5-flash',
            'gemini-2.0-flash',
            'gemini-2.0-flash-lite',
        ]
        
        # Tạo Prompt gửi cho Gemini
        prompt = f"""
        Tôi đang quản lý một dự án có tên là: "{self.name}".
        Hãy đóng vai là một chuyên gia quản lý dự án, phân tích và gợi ý cho tôi danh sách từ 5 đến 7 công việc chi tiết cần thực hiện cho dự án này.
        
        Trả lời BẮT BUỘC chỉ bằng một Object JSON nguyên chất, định dạng chính xác phân tích cú pháp được, với cấu trúc như sau:
        {{
            "tasks": [
                {{
                    "name": "Tên công việc 1", 
                    "description": "Mô tả ngắn gọn",
                    "sop": "<p>Văn bản HTML chi tiết quy trình thực hiện bước 1, bước 2...</p>",
                    "checklist": "Nội dung 1, Nội dung 2, Nội dung 3"
                }},
                {{
                    "name": "Tên công việc 2", 
                    "description": "Mô tả ngắn gọn",
                    "sop": "<p>Văn bản HTML quy trình...</p>",
                    "checklist": "Nội dung A, Nội dung B"
                }}
            ]
        }}
        Lưu ý: 
        - "sop" là quy trình thực hiện chi tiết (Standard Operating Procedure) dưới dạng HTML.
        - "checklist" là các đầu mục kiểm tra nhỏ, phân tách bằng dấu phẩy.
        Không có thêm bất kỳ văn bản nào khác ngoài Object JSON này.
        """
        
        headers = {'Content-Type': 'application/json'}
        data = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        
        try:
            # Thử lần lượt các model cho đến khi tìm được model khả dụng
            last_error = None
            response = None
            for model_name in model_candidates:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
                try:
                    response = requests.post(url, headers=headers, data=json.dumps(data), timeout=30)
                except Exception as e:
                    last_error = str(e)
                    response = None
                    continue
                
                if response.status_code == 200:
                    break  # Tìm được model hoạt động
                elif response.status_code == 429:
                    last_error = f"Model {model_name} hết hạn mức (429)."
                    time.sleep(5)
                    continue
                elif response.status_code == 404:
                    last_error = f"Model {model_name} không tìm thấy (404)."
                    continue
                else:
                    last_error = f"Lỗi từ model {model_name}: {response.status_code}"
                    continue

            if not response or response.status_code != 200:
                raise UserError(_(
                    "Tất cả các model AI đều đang bận hoặc hết hạn mức.\n\n"
                    "Giải pháp:\n"
                    "1. Vui lòng đợi khoảng 1 phút rồi nhấn lại nút Gợi ý.\n"
                    "2. Hoặc cấu hình API Key mới trong Thông số hệ thống.\n\n"
                    f"Chi tiết: {last_error}"
                ))
            
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
                    
                    # Thay vì tạo Task ngay, Ta tạo Data cho Wizard
                    wizard_lines = []
                    for task_dict in tasks_data:
                        task_name = task_dict.get('name')
                        if task_name:
                            wizard_lines.append((0, 0, {
                                'name': task_name,
                                'description': task_dict.get('description', ''),
                                'ai_sop': task_dict.get('sop', ''),
                                'checklist_raw': task_dict.get('checklist', ''),
                            }))
                            
                    if wizard_lines:
                        # Tạo bản ghi Wizard trong RAM
                        wizard = self.env['ai.task.generator.wizard'].create({
                            'project_id': self.id,
                            'line_ids': wizard_lines
                        })
                        
                        # Trả về Action mở Popup Wizard để User sửa
                        return {
                            'name': _('Check & Edit Gợi ý Của AI'),
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
                
        except requests.exceptions.Timeout:
            raise UserError(_("Kết nối tới Gemini API bị quá hạn (Timeout). Vui lòng thử lại sau."))
        except requests.exceptions.ConnectionError:
            raise UserError(_("Không thể kết nối đến Gemini API. Vui lòng kiểm tra lại mạng."))
        except Exception as e:
            raise UserError(_(f"Có lỗi bất ngờ xảy ra khi dùng AI:\n{str(e)}"))

