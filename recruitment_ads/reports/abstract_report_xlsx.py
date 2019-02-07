from odoo import models, fields


class WorkBookSheet:
    def __init__(self, parentcls, name, sheet, columns, row_pos=0):
        self.parentcls = parentcls
        self.name = name
        self.sheet = sheet
        self.columns = columns
        self.row_pos = row_pos

    def _set_column_width(self):
        for position, column in self.columns.items():
            self.sheet.set_column(position, position, column['width'])

    def _write_report_name(self):
        self.sheet.merge_range(
            self.row_pos, 0, self.row_pos, len(self.columns) - 1,
            self.name, self.parentcls.format_bold
        )
        self.row_pos += 3

    def write_array_title(self, title):
        self.sheet.merge_range(
            self.row_pos, 0, self.row_pos, len(self.columns) - 1,
            title, self.parentcls.format_bold
        )
        self.row_pos += 1

    def write_array_header(self):
        for col_pos, column in self.columns.items():
            self.sheet.write(self.row_pos, col_pos, column['header'],
                             self.parentcls.format_header_center)
        self.row_pos += 1

    def write_line(self, line_object):
        for col_pos, column in self.columns.items():
            value = getattr(line_object, column['field'], False)
            cell_type = column.get('type', 'string')
            if cell_type == 'many2one':
                if value:
                    self.sheet.write_string(
                        self.row_pos, col_pos, value.name or '')
                else:
                    self.sheet.write_string(self.row_pos, col_pos, '')
            elif cell_type == 'x2many':
                if value:
                    self.sheet.write_string(
                        self.row_pos, col_pos, '•' + '\r\n•'.join(value.mapped('name')) or '')
                else:
                    self.sheet.write_string(self.row_pos, col_pos, '')
            elif cell_type == 'string':
                self.sheet.write_string(self.row_pos, col_pos, value or '')
            elif cell_type == 'amount':
                if value:
                    self.sheet.write_number(
                        self.row_pos, col_pos, float(value), self.parentcls.format_amount
                    )
                else:
                    self.sheet.write_string(self.row_pos, col_pos, '')
            elif cell_type == 'datetime':
                if value:
                    datetime_value = fields.Datetime.from_string(value)
                    datetime_value = fields.Datetime.context_timestamp(line_object, datetime_value)
                    datetime_value = fields.Datetime.to_string(datetime_value)
                    self.sheet.write_string(
                        self.row_pos, col_pos, datetime_value or '')
                else:
                    self.sheet.write_string(self.row_pos, col_pos, '')
            elif cell_type == 'bool':
                values = column.get('values', False)
                if values:
                    self.sheet.write_string(
                        self.row_pos, col_pos, values[value])
                else:
                    if value:
                        self.sheet.write_string(
                            self.row_pos, col_pos, 'yes')
                    else:
                        self.sheet.write_string(
                            self.row_pos, col_pos, 'no')

        self.row_pos += 1

class AbstractReportXslx(models.AbstractModel):
    _name = 'report.recruitment_ads.abstract_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def __init__(self, pool, cr):
        # main sheet which will contains report
        self.sheets = None

        # Formats
        self.format_right = None
        self.format_right_bold_italic = None
        self.format_bold = None
        self.format_header_left = None
        self.format_header_center = None
        self.format_header_right = None
        self.format_header_amount = None
        self.format_amount = None
        self.format_percent_bold_italic = None

    def _get_report_sheets(self,report):
        raise NotImplementedError()

    def _add_sheets(self, workbook,report):
        all_sheets = self._get_report_sheets(report)
        for sheet in all_sheets:
            for title, columns in sheet.items():
                work_sheet = workbook.add_worksheet(title[:31])
                self.sheets.append(WorkBookSheet(self, title, work_sheet, columns))

    def _get_sheet_by_name(self, name):
        return filter(lambda sheet: sheet.name == name, self.sheets).__next__()

    def get_workbook_options(self):
        return {'constant_memory': True}

    def generate_xlsx_report(self, workbook, data, objects):
        self.sheets = []
        report = objects

        self._define_formats(workbook)

        self._add_sheets(workbook,report)

        self._set_column_width()

        #self._write_report_name()

        self._generate_report_content(workbook, report)

    def _define_formats(self, workbook):
        """ Add cell formats to current workbook.
        Those formats can be used on all cell.

        Available formats are :
         * format_bold
         * format_right
         * format_right_bold_italic
         * format_header_left
         * format_header_center
         * format_header_right
         * format_header_amount
         * format_amount
         * format_percent_bold_italic
        """
        self.format_bold = workbook.add_format({'bold': True})
        self.format_right = workbook.add_format({'align': 'right'})
        self.format_right_bold_italic = workbook.add_format(
            {'align': 'right', 'bold': True, 'italic': True}
        )
        self.format_header_left = workbook.add_format(
            {'bold': True,
             'border': True,
             'bg_color': '#FFFFCC'})
        self.format_header_center = workbook.add_format(
            {'bold': True,
             'align': 'center',
             'border': True,
             'bg_color': '#FFFFCC'})
        self.format_header_right = workbook.add_format(
            {'bold': True,
             'align': 'right',
             'border': True,
             'bg_color': '#FFFFCC'})
        self.format_header_amount = workbook.add_format(
            {'bold': True,
             'border': True,
             'bg_color': '#FFFFCC'})
        self.format_header_amount.set_num_format('#,##0.00')
        self.format_amount = workbook.add_format()
        self.format_amount.set_num_format('#,##0.00')
        self.format_percent_bold_italic = workbook.add_format(
            {'bold': True, 'italic': True}
        )
        self.format_percent_bold_italic.set_num_format('#,##0.00%')

    def _set_column_width(self):
        """Set width for all defined columns.
        Columns are defined with `_get_report_columns` method.
        """
        for sheet in self.sheets:
            sheet._set_column_width()

    def _write_report_name(self):
        """Write report title on current line using all defined columns width.
        Columns are defined with `_get_report_columns` method.
        """
        for sheet in self.sheets:
            sheet._write_report_name()
            break

    def write_array_title(self, title, sheet_name):
        """Write array title on current line using all defined columns width.
        Columns are defined with `_get_report_columns` method.
        """
        sheet = self._get_sheet_by_name(sheet_name)
        sheet.write_array_title(title)

    def write_array_header(self, sheet_name=None):
        """Write array header on current line using all defined columns name.
        Columns are defined with `_get_report_columns` method.
        """
        if sheet_name:
            sheet = self._get_sheet_by_name(sheet_name)
            sheet.write_array_header()
        else:
            for sheet in self.sheets:
                sheet.write_array_header()

    def write_line(self, line_object, sheet_name):
        """Write a line on current line using all defined columns field name.
        Columns are defined with `_get_report_columns` method.
        """
        sheet = self._get_sheet_by_name(sheet_name)
        sheet.write_line(line_object)

    def _generate_report_content(self, workbook, report):
        pass

    def _get_report_name(self):
        """
            Allow to define the report name.
            Report name will be used as sheet name and as report title.

            :return: the report name
        """
        raise NotImplementedError()