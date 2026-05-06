import tempfile
import binascii
import xlrd
import logging
_logger = logging.getLogger(__name__)
from odoo import models, fields, _
from odoo.exceptions import UserError
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
import re


class ImportTrailBalances(models.TransientModel):
    _name = 'import.trial.balances'

    xls_file_name = fields.Char('Excel File Name', size=64, required=True)
    xls_file = fields.Binary('Excel File')
    difference_account_id = fields.Many2one('account.account', 'Difference Account', required=True, default=lambda self: self._default_account_id())
    date = fields.Date('Date', required=True)

    def _default_account_id(self):
        default_account_id = self.env['account.account'].search([('code', '=', 999999)], limit=1)
        return default_account_id.id if default_account_id else False



    def import_trial_balance_data(self):

        try:
            file_string = tempfile.NamedTemporaryFile(suffix=".xlsx")
            file_string.write(binascii.a2b_base64(self.xls_file))
            book = xlrd.open_workbook(file_string.name)


        except:
            raise UserError(_("Please choose the .xlsx file"))

        for sheet in book.sheets():

            try:
                iteration_count = 0
                new_line_ids = []
                total_debit = 0.00
                total_credit = 0.00
                default_journal = self.env['account.journal'].search([('name', '=', 'Opening Journal')])

                if sheet.name == 'Sheet1':

                    # excluded_accounts = ['1050','2010','2011','1051','1020','1040','1052','1060','6306']


                    for row in range(sheet.nrows):
                        iteration_count += 1
                        _logger.info("Iteration: %s", iteration_count)
                        if row >= 7:
                            row_values = sheet.row_values(row)

                            account = row_values[0]


                            if account:
                                try:
                                    account = int(account)

                                except ValueError:
                                    print("Error: account is not a valid number, skipping this row.")
                                    continue

                            else:
                                print("Error: account is empty, skipping this row.")
                                continue

                            debit = row_values[3]

                            credit = row_values[4]

                            account_id = self.env['account.account'].search([('code', '=', str(account))])

                            if account_id:

                                # if account_id.code not in excluded_accounts:

                                    if debit:
                                        debit_line = (0, 0, {
                                            'account_id': account_id.id,
                                            'name': row_values[1],
                                            'debit': debit,
                                        })

                                        total_debit += debit

                                        new_line_ids.append(debit_line)

                                    elif credit:
                                        credit_line = (0, 0, {
                                            'account_id': account_id.id,
                                            'name': row_values[4],
                                            'credit': credit
                                        })

                                        total_credit += credit

                                        new_line_ids.append(credit_line)


                            # else:
                            #     print("not prsent account=============",account_id)

                    if total_debit == total_credit:
                        journal_entry_creation = self.env['account.move'].create({
                            'date': self.date,
                            'ref': 'Opening Entry',
                            'move_type': 'entry',
                            'journal_id': default_journal.id,
                            'line_ids': new_line_ids
                        })

                    else:
                        difference_amount = abs(total_debit - total_credit)

                        if total_debit > total_credit:
                            difference_amount_line = {
                                'account_id': self.difference_account_id.id,
                                'name': 'Difference Account',
                                'debit': 0.00,
                                'credit': difference_amount
                            }

                        else:
                            difference_amount_line = {
                                'account_id': self.difference_account_id.id,
                                'name': 'Difference Account',
                                'debit': difference_amount,
                                'credit': 0.00
                            }


                        new_line_ids.append((0, 0, difference_amount_line))

                        journal_entry_creation = self.env['account.move'].create({
                            'date': self.date,
                            'ref': 'Opening Entry',
                            'move_type': 'entry',
                            'journal_id': default_journal.id,
                            'line_ids': new_line_ids,
                            'imported_invoices': True
                        })
                        # journal_entry_creation.action_post()





            except IndexError:
                pass


