- Managers higher up in the hierarchy cannot modify or refuse a time off that
  has already begun and is no longer pending of the first approval, while the
  direct time off approver can. Odoo performs this check inline in
  `hr.leave.write()`, comparing with the employee's time off manager, so it
  cannot be extended without bypassing the standard write checks.
