from odoo import api, fields, models, _


class HolidaysAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    @api.depends('number_of_days', 'employee_id')
    def _compute_number_of_hours_display(self):
        for allocation in self:
            if allocation.number_of_days:
                allocation.number_of_hours_display = allocation.number_of_days * allocation.employee_id.sudo().resource_id.calendar_id.hours_per_day
            else:
                allocation.number_of_hours_display = 0.0