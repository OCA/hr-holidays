# Copyright 2023 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)


from odoo import fields, models


class HrLeaveType(models.Model):
    _inherit = "hr.leave.type"

    can_overlap = fields.Boolean("Allow overlap with other leaves")

    def _get_employees_days_per_allocation(self, employee_ids, date=None):
        """Remove overlapping days"""
        HrLeave = self.env["hr.leave"]

        result = super()._get_employees_days_per_allocation(employee_ids, date=date)

        if not date:
            date = fields.Date.to_date(
                self.env.context.get("default_date_from")
            ) or fields.Date.context_today(self)

        for employee_id in employee_ids:
            for possible_overlap in HrLeave.search(
                [
                    ("employee_id", "=", employee_id),
                    ("state", "=", "validate"),
                    ("holiday_status_id.can_overlap", "=", True),
                ]
            ):
                for overlap in HrLeave.search(
                    [
                        ("employee_id", "=", employee_id),
                        ("state", "in", ("confirm", "validate1", "validate")),
                        ("id", "not in", possible_overlap.ids),
                        ("date_from", "<=", possible_overlap.date_to),
                        ("date_to", ">=", possible_overlap.date_from),
                        ("holiday_status_id", "in", self.ids),
                    ]
                ):
                    allocation_dict = result[employee_id][overlap.holiday_status_id]
                    number_of_days = overlap.employee_id._get_work_days_data_batch(
                        possible_overlap.date_from
                        if possible_overlap.date_from >= overlap.date_from
                        else overlap.date_from,
                        possible_overlap.date_to
                        if possible_overlap.date_to <= overlap.date_to
                        else overlap.date_to,
                        compute_leaves=False,
                    )[employee_id]["days"]
                    for allocation, allocation_days in allocation_dict.items():
                        if (
                            not allocation
                            or isinstance(allocation, str)
                            or allocation.date_to
                            and (
                                allocation.date_to < date or allocation.date_from > date
                            )
                        ):
                            continue
                        allocation_days["virtual_remaining_leaves"] += number_of_days
                        allocation_days["virtual_leaves_taken"] -= number_of_days
                        if possible_overlap.state == "validate":
                            allocation_days["remaining_leaves"] += number_of_days
                            allocation_days["leaves_taken"] -= number_of_days
                        break
                    if "error" in allocation_dict:
                        allocation_dict["error"][
                            "virtual_remaining_leaves"
                        ] += number_of_days
                        allocation_dict[False][
                            "virtual_remaining_leaves"
                        ] += number_of_days
                        if not allocation_dict["error"]["virtual_remaining_leaves"]:
                            del allocation_dict["error"]
                            del allocation_dict[False]
        return result
