Currently, leave types that allow negative balances require a numeric limit to
be defined. But originally, this module allowed for an "unlimited" negative
balance.
A common and useful workaround is to use a very large number, but this is not
ideal. In the future, it would be interesting to introduce an option for
endless negative credit, removing the need to set an arbitrary upper limit.
