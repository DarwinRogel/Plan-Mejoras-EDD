from odoo import models, api
from datetime import datetime

class ReportePlanMejoras(models.AbstractModel):
    _name = "report.plan_mejoras.report_plan_mejoras"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["pm.plan"].browse(docids)
        docargs = {
            "docs":docs,
            "fecha":datetime.now().strftime("%m-%d-%Y"),
        }
        return docargs