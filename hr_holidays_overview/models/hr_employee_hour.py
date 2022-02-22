# Copyright 2022 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import api, fields, models

TYPE_SELECTION = [
    ("leave_request", "Leave Request"),
    ("leave_allocation", "Leave Allocation"),
]
ONDELETE_SELECTION = {
    "leave_request": "set default",
    "leave_allocation": "set default",
}

_logger = logging.getLogger(__name__)


class HrEmployeeHour(models.Model):
    _inherit = "hr.employee.hour"

    type = fields.Selection(selection_add=TYPE_SELECTION, ondelete=ONDELETE_SELECTION)
    leave_state = fields.Selection(
        [
            ("draft", "To Submit"),
            ("cancel", "Cancelled"),
            ("confirm", "To Approve"),
            ("refuse", "Refused"),
            ("validate1", "Second Approval"),
            ("validate", "Approved"),
        ],
        "State",
    )

    @api.model
    def search_allocations_domain(self, employee):
        return [
            ("employee_id", "=", employee.id),
            ("state", "not in", ("draft", "cancel", "refuse")),
            ("date_from", ">=", employee.last_hours_report_date),
        ]

    @api.model
    def search_requests_domain(self, employee):
        """ Search filter rules for requests """
        return [
            ("employee_id", "=", employee.id),
            ("state", "not in", ("draft", "cancel", "refuse")),
            ("date_from", ">=", employee.last_hours_report_date),
        ]

    @api.model
    def _prepare_leave_allocation_values(self, employee, date_from=None, date_to=None):
        """Retrieve leave allocations values

        :param employee: an employee record
        :param date_from: a datetime.date object (default first contract date, included)
        :param date_to: a datetime.date object (default today, included)
        """
        hla_model = self.env["hr.leave.allocation"]
        search_domain = self.search_allocations_domain(employee)
        allocations = hla_model.search(search_domain)
        values_list = []
        for allocation in allocations:
            days_qty = allocation.number_of_days
            hours_qty = allocation.number_of_hours_display
            values_list.append(
                {
                    "date": allocation.date_from,
                    "name": allocation.holiday_status_id.name,
                    "employee_id": employee.id,
                    "model_name": hla_model._name,
                    "res_id": allocation.id,
                    "type": "leave_allocation",
                    "hours_qty": hours_qty,
                    "days_qty": days_qty,
                    "leave_state": allocation.state,
                }
            )
        return values_list

    @api.model
    def _prepare_leave_request_values(self, employee):
        """Retrieve leave requests values

        :param employee: an employee record
        :param date_from: a datetime.date object (default first contract date, included)
        :param date_to: a datetime.date object (default today, included)
        """
        hl_model = self.env["hr.leave"]
        search_domain = self.search_requests_domain(employee)
        requests = hl_model.search(search_domain)
        values_list = []
        for request in requests:
            days_qty = request.number_of_days
            hours_qty = request.number_of_hours_display
            holiday_status_id = request.holiday_status_id
            values_list.append(
                {
                    "date": request.date_from,
                    "name": holiday_status_id.name,
                    "employee_id": employee.id,
                    "model_name": hl_model._name,
                    "res_id": request.id,
                    "type": "leave_request",
                    "hours_qty": hours_qty,
                    "days_qty": days_qty,
                    "leave_state": request.state,
                    "unplanned": holiday_status_id.allocation_type == "no",
                }
            )
        return values_list

    def _create_values_per_employee(self, employee, date):
        super()._create_values_per_employee(employee, date)
        # For leaves and holidays, we need to have a whole year view
        leave_alloc_values = self._prepare_leave_allocation_values(employee)
        leave_request_values = self._prepare_leave_request_values(employee)
        self.create(leave_request_values + leave_alloc_values)
        return
