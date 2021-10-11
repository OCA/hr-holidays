from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)

class HolidaysAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    # fields
    remaining_leaves = fields.Float(compute='_compute_remaining_leaves')

    def _compute_remaining_leaves(self):
        for allocation in self:

            # Get number of days for all validated leaves filtered by employee and leave type
            leaves = self.env['hr.leave'].search([
                ('employee_id', '=', allocation.employee_id.id),
                ('state', '=', 'validate'),
                ('holiday_status_id', '=',  allocation.holiday_status_id.id)
            ])
            allocation.remaining_leaves = allocation.number_of_days - sum(leaves.mapped('number_of_days'))