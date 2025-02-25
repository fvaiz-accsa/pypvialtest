from odoo import models, fields, api

#import suds (para Cotizacion USD(
from suds.client import Client


class CustomCurrencyRate(models.Model):
    _inherit = 'res.currency.rate'
    # test = fields.Char(string='Test')
    def test_create(self):
        fecha = '2021-08-06'
        #curr_id = self.env['res.currency.rate'].search([('rate', '=', 1)], limit=1).currency_id
        #print(curr_id)
        res_curr = {
            'name': fecha,
            'rate': 43.01,
            'currency_id': 46,
            'company_id': 1
        }
        print(res_curr)
        self.env['res.currency.rate'].create(res_curr)

    def test_WS(self):
        client = Client('https://cotizaciones.bcu.gub.uy/wscotizaciones/servlet/awsbcucotizaciones?wsdl')
        cotiza = client.factory.create('wsbcucotizacionesin')
        cotiza.FechaDesde = '2021-07-22 12:00:00'
        cotiza.FechaHasta = '2021-07-22 23:00:00'
        cotiza.Grupo = 2
        cotiza.Moneda = {'item': [2225]}
        ret = client.service.Execute(cotiza)
        cotizaciones = str(ret.datoscotizaciones)
        print(float(cotizaciones[250:256]))
        print(float(cotizaciones[272:278]))

    def test_Create_WS(self):
        # 1: Obtener ultima fecha de cotizacion
        client1 = Client("https://cotizaciones.bcu.gub.uy/wscotizaciones/servlet/awsultimocierre?wsdl")
        ultimo_obj = client1.factory.create("wsultimocierreout")
        ret1 = client1.service.Execute()
        ultima_fecha = str(ret1)[32:42]
        print(ultima_fecha)

        # 2: Buscar ultima cotizacion en esa fecha en odoo
        last_cotizacion = self.env['res.currency.rate'].search([('name', '=', ultima_fecha)])
        print(last_cotizacion)

        # 3: Si no existe cotizacion para esa fecha crear registro
        if last_cotizacion.name == False:
            print("vacio")
            client = Client('https://cotizaciones.bcu.gub.uy/wscotizaciones/servlet/awsbcucotizaciones?wsdl')
            cotiza = client.factory.create('wsbcucotizacionesin')
            cotiza.FechaDesde = ultima_fecha + ' 12:00:00'
            cotiza.FechaHasta = ultima_fecha + ' 23:00:00'
            cotiza.Grupo = 2
            cotiza.Moneda = {'item': [2225]}
            ret = client.service.Execute(cotiza)
            cotizaciones = str(ret.datoscotizaciones)
            print(float(cotizaciones[250:256]))
            print(float(cotizaciones[272:278]))
            cotizacion = float(cotizaciones[250:256])

            res_curr = {
                'name': ultima_fecha,
                'rate': 1/cotizacion,
                'currency_id': 2,
                'company_id': 1
            }
            self.env['res.currency.rate'].create(res_curr)
        else:
            print('search()', last_cotizacion, last_cotizacion.name)

# PURCHARSE - purchase.order
class CustomSaleOrder(models.Model):
    _inherit = 'purchase.order'
    proyecto = fields.Many2one(string='Obra/Proyecto', comodel_name='account.analytic.account')
    autorizado = fields.Text(string='Autorizado')

    def onChange_Proyecto(self, pedido):
        pedidoLine = self.env['purchase.order.line'].search([('order_id', '=', pedido.id)])
        for line in pedidoLine:
            line.write({
               'account_analytic_id': pedido.proyecto
            })

    def write(self, vals):
        print(vals)
        print(self.id)
        if 'proyecto' in vals:
            pedidoLine = self.env['purchase.order.line'].search([('order_id', '=', self.id)])
            for line in pedidoLine:
                line.write({
                    'account_analytic_id': vals['proyecto']
                })
        res = super(CustomSaleOrder, self).write(vals)
        return res

class CustomPurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.model
    def create(self, vals):
        #print('Pedido Id', vals['order_id'])
        #print('Name ', vals['name'])
        pedido = self.env['purchase.order'].browse([vals['order_id']])
        vals['account_analytic_id'] = pedido.proyecto.id
        res = super(CustomPurchaseOrderLine, self).create(vals)
        return res

# Cambios desde el 27/9
# class CustomSaleOrder(models.Model):
#     _inherit = 'sale.order'
#     leyesSociales = fields.Monetary(string='Leyes Sociales')