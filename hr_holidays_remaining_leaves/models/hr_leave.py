from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)
from odoo.tools.float_utils import float_round

class HolidaysAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    # fields
    remaining_leaves = fields.Float(compute='_compute_remaining_leaves')
    remaining_leaves_display = fields.Char('Remaining (Days/Hours)', compute='_compute_remaining_leaves_display')

    def _compute_remaining_leaves(self):
        for allocation in self:

            # Get number of days for all validated leaves filtered by employee and leave type
            leaves = self.env['hr.leave'].search([
                ('employee_id', '=', allocation.employee_id.id),
                ('state', '=', 'validate'),
                ('holiday_status_id', '=',  allocation.holiday_status_id.id)
            ])
            allocation.remaining_leaves = allocation.number_of_days - sum(leaves.mapped('number_of_days'))
    
    def _compute_remaining_leaves_display(self):
        for allocation in self:
            allocation.remaining_leaves_display = '%g %s' % (float_round(allocation.remaining_leaves, precision_digits=2), _('days'))