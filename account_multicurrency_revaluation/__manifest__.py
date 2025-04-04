# Copyright 2012-2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Multicurrency revaluation",
    "version": "0.1",
    "category": "Finance",
    "summary": "Manage revaluation for multicurrency environment",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-closing",
    "license": "AGPL-3",
    "depends": ["account"],
    "demo": ["demo/account_demo.xml", "demo/currency_demo.xml"],
    "data": [
        "views/res_config_view.xml",
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/account_view.xml",
        "views/account_move_views.xml",
        "views/account_move_line_views.xml",
        "wizard/print_currency_unrealized_report_view.xml",
        "wizard/wizard_currency_revaluation_view.xml",
        "wizard/wizard_reverse_currency_revaluation_view.xml",
        "report/report.xml",
        "report/unrealized_currency_gain_loss.xml",
    ],
    "assets": {
        "web.report_assets_common": [
            "account_multicurrency_revaluation/static/src/css/reports.css",
        ],
    },
    "installable": True,
}
