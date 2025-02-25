# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict
import time
import re
import logging

from psycopg2 import errors as pgerrors

from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, mute_logger
from odoo.exceptions import ValidationError, UserError
from odoo.addons.base.models.res_partner import WARNING_MESSAGE, WARNING_HELP
from odoo.tools import SQL, unique
from odoo.addons.base_vat.models.res_partner import _ref_vat

_logger = logging.getLogger(__name__)



class ResPartner(models.Model):
    _inherit = "res.partner"
    
    
    is_coa_installed = fields.Boolean(store=False, default=lambda partner: bool(partner.env.company.chart_template))