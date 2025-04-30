from odoo import SUPERUSER_ID, api
from odoo.tools.sql import column_exists, table_exists
import logging
_logger = logging.getLogger(__name__)


def migrate(cr, version=None):
    env = api.Environment(cr, SUPERUSER_ID, {})

    _logger.info("------*** ELIMINANDO MODULOS QUE NO EXISTEN ***------")
    models_to_del = [
        'account_group_hierarchy',
        'account_multicurrency_revaluation',
        'account_reconciliation_widget',
        'accounting_pdf_reports',
        'ajedrez_xrm',
        'fc_pyp',
        'fc_pyp_add',
        'fc_pyp_add_2303',
        'om_account_accountant',
        'om_account_asset',
        'om_account_budget',
        'om_account_daily_reports',
        'om_account_bank_statement_import',
        'om_account_followup',
        'om_credit_limit',
        'om_fiscal_year',
        'om_recurring_payments',
        'partner_statement',
        'stock_barcodes',
        'web_environment_ribbon',
        'web_pwa_oca',
        'web_responsive',
        'web_widget_numeric_step',
    ]

    env.cr.execute("""DELETE FROM ir_module_module WHERE name IN %s;""", [tuple(models_to_del)])

    del_from_tables = [
        ('ir.ui.view', ['ir_ui_view']),
        ('ir.actions.act_window', ['ir_act_window', 'ir_actions']),
        ('ir.ui.menu', ['ir_ui_menu'])
    ]
    for module in models_to_del:
        _logger.info("------*** ELIMINANDO VISTAS, MENUS Y ACTIONS: MODULO %s ***------" % module)
        for model, tables in del_from_tables:
            for table in tables:
                if model == 'ir.ui.menu':  # Eliminar menus hijos
                    env.cr.execute("""
                        DELETE FROM ir_ui_menu WHERE parent_id IN (
                            SELECT id FROM ir_ui_menu WHERE parent_id IN (
                                SELECT res_id FROM ir_model_data
                                WHERE model = '%s' AND module = '%s'
                            )
                        );
                    """ % (model, module))
                    env.cr.execute("""
                        DELETE FROM %s WHERE parent_id IN (
                            SELECT res_id FROM ir_model_data
                            WHERE model = '%s' AND module = '%s'
                        );
                    """ % (table, model, module))
                if model == 'ir.ui.view':  # Eliminar vistas hijas
                    env.cr.execute("""
                        DELETE FROM %s WHERE inherit_id IN (
                            SELECT res_id FROM ir_model_data
                            WHERE model = '%s' AND module = '%s'
                        );
                    """ % (table, model, module))
                env.cr.execute("""
                    DELETE FROM %s WHERE id IN (
                        SELECT res_id FROM ir_model_data
                        WHERE model = '%s' AND module = '%s'
                    );
                """ % (table, model, module))
            env.cr.execute("""
                DELETE FROM ir_model_data WHERE model = '%s' AND module = '%s';
            """ % (model, module))

        _logger.info("------*** ELIMINANDO IR.MODEL.DATA: MODULO %s ***------" % module)
        module_prefix = 'module_' + module
        env.cr.execute("""DELETE FROM ir_model_data WHERE name = '%s';""" % module_prefix)
        env.cr.execute("""DELETE FROM ir_model_data WHERE module = '%s';""" % module)
   










#pyp_vial_mig_3