from odoo import models, fields, api
from zeep import Client
from zeep.wsse.username import UsernameToken
import xml.etree.ElementTree as ET
import pathlib
import os
import base64
from odoo.exceptions import ValidationError, UserError

class fe_UCFE(models.Model):
    _inherit = 'account.move'

    tipoCFE = fields.Selection([('111', 'e-Factura')], string='Tipo Comprobante')
    info = fields.Text(string='Info')
    customerRUT = fields.Char(string='Documento', related='partner_id.vat')
    tipoDoc = fields.Selection(string='Tipo Doc.', related='partner_id.x_tipoDoc')
    formaPago = fields.Selection([('1', 'Contado'), ('2', 'Crédito')], string='Forma de Pago')
    Number = fields.Char(string='Number')
    RtaMessage = fields.Char(string='RtaMessage')
    RtaCode = fields.Char(string='RtaCode')
    Series = fields.Char(string='Series')
    Uuid = fields.Char(string='Identificador')
    xmlText = fields.Text(string='XML')
    feEstado = fields.Selection([('0', 'VALIDA'), ('-1', 'Error en el servidor'), ('1', 'Denegado'),
                                 ('3', 'Comercio inválido'), ('5', 'CFE rechazado por DGI'), ('11', 'Enviada'),
                                 ('12', 'Requerimiento inválido'),('30', 'Error en formato'),('31', 'Error en formato de CFE'),
                                 ('89', 'Terminal inválida'),('96', 'Error en sistema'),('99', 'Sesión no iniciada'),
                                 ('100', 'Error Desconocido')],
                                string='Estado DGI')
    tipoCFE_FC_NC = fields.Selection(
        [('112', 'Nota de Crédito de e-Factura')],
        string='Tipo Comp. NC')

    cfe_emitidas = fields.One2many('fc_pyp.fe_line', 'cfe_id', 'Doc. Electrónico' )
    cfe_serieNumero = fields.Text(string='Numero')
    talon_Fisico = fields.Char(string='Talonario Físico')
    matricula = fields.Char(string='Matrícula')
    km = fields.Integer(string='Km')
    funcionario = fields.Char(string='Funcionario')
    mensaje_USD = fields.Char(string='*', default='Recuerde cambiar la cuenta deudora/acreedora por una en Dolares!')

    #fields.Many2one('res.currency', string='Calculo')

    # x_account = fields.Many2one('account.account', 'Cuenta', domain="['&', ('currency_id.id','=','2'), ('user_type_id.id', '=', '1')]")
    # x_account_hide = fields.Boolean('HideAccount', default=False)
    # x_account_ant = fields.Text(string='Account_ant')

    #Confirmar Factura / Nota de Credito
    def action_post(self):
        res = super(fe_UCFE, self).action_post()
        try:
            # Validar cuenta USD
            db_name = self.env.cr.dbname
            val = False
            if db_name != "xProd_20230829":
              val = self.validarCurrency()
            if (val == True):
                mensaje = self.mensajeValidarCuerrency()
                raise ValidationError(mensaje)
            # Facturacion Electronica
            if (self.tipoCFE != False and self.tipoCFE_FC_NC == False):
                mensaje = self.camposObligatorios()
                if(mensaje != ''):
                    raise ValidationError('No se puede Confirmar, los siguientes campos son obligatorios: \n' + mensaje)
                #self.emitirIssueCFE()
                self.emitirCFE()
            elif (self.tipoCFE_FC_NC != False):
                self.emitirCFE()
        except Exception as e:
            raise ValidationError('Error: ' + str(e))
        else:
            return res


    def emitirIssueCFE(self):
        # Configuracion de FE Memory
        conf = self.env['fc_pyp.settings_fc'].search([('activo', '=', 'True')])

        # Cliente Country y State
        cliente = self.env['res.partner'].browse([self.partner_id.id])
        stateCliente = self.env['res.country.state'].browse([cliente.state_id.id])
        country = self.env['res.country'].browse([cliente.country_id.id])

        # Currency
        moneda = self.env['res.currency'].browse([self.currency_id.id])

        # Empresa
        empresa = self.env['res.company'].browse([self.env.company.id])

        # Totales
        mntNoGrv = 0
        mntNetoIvaTasaMin = 0
        mntNetoIVATasaBasica = 0

        #########
        #path = str(pathlib.Path().resolve()) + '/XML_Template'
        path = str(os.path.dirname(__file__))
        tree = ET.parse(os.path.join(path, 'TemplateCFE_Total.xml'))
        root = tree.getroot()
        prodnum = 0
        # XML Path
        IdDoc_Path = './{http://cfe.dgi.gub.uy}eFact/{http://cfe.dgi.gub.uy}Encabezado/{http://cfe.dgi.gub.uy}IdDoc/{http://cfe.dgi.gub.uy}'
        Emisor_Path = './{http://cfe.dgi.gub.uy}eFact/{http://cfe.dgi.gub.uy}Encabezado/{http://cfe.dgi.gub.uy}Emisor/{http://cfe.dgi.gub.uy}'
        Receptor_Path = './{http://cfe.dgi.gub.uy}eFact/{http://cfe.dgi.gub.uy}Encabezado/{http://cfe.dgi.gub.uy}Receptor/{http://cfe.dgi.gub.uy}'
        Totales_Path = './{http://cfe.dgi.gub.uy}eFact/{http://cfe.dgi.gub.uy}Encabezado/{http://cfe.dgi.gub.uy}Totales/{http://cfe.dgi.gub.uy}'

        ## Encabezado - IdDoc
        if(self.move_type == 'out_refund'):
            for x in root.findall(IdDoc_Path + 'TipoCFE'):
                x.text = str(self.tipoCFE_FC_NC)
        else:
            for x in root.findall(IdDoc_Path + 'TipoCFE'):
                x.text = str(self.tipoCFE)
        for x in root.findall(IdDoc_Path + 'FchEmis'):
            x.text = str(self.invoice_date)
        for x in root.findall(IdDoc_Path + 'FmaPago'):
            x.text = str(self.formaPago)

        ## Encabezado - Emisor
        for x in root.findall(Emisor_Path + 'RUCEmisor'):
            x.text = str(empresa.vat)
        for x in root.findall(Emisor_Path + 'RznSoc'):
            x.text = str(empresa.name)
        for x in root.findall(Emisor_Path + 'CdgDGISucur'):
            x.text = str(empresa.company_registry)
        for x in root.findall(Emisor_Path + 'DomFiscal'):
            x.text = str(empresa.street)
        for x in root.findall(Emisor_Path + 'Ciudad'):
            x.text = str(empresa.city)
        for x in root.findall(Emisor_Path + 'Departamento'):
            x.text = self.env['res.country.state'].browse([cliente.state_id.id]).name

        ## Encabezado - Receptor
        for x in root.findall(Receptor_Path + 'TipoDocRecep'):
            x.text = str(cliente.x_tipoDoc)
        for x in root.findall(Receptor_Path + 'CodPaisRecep'):
            x.text = country.code
        for x in root.findall(Receptor_Path + 'DocRecep'):
            x.text = str(cliente.vat)
        for x in root.findall(Receptor_Path + 'RznSocRecep'):
            x.text = cliente.name
        for x in root.findall(Receptor_Path + 'DirRecep'):
            x.text = cliente.street
        for x in root.findall(Receptor_Path + 'CiudadRecep'):
            x.text = cliente.city

        # Items
        for prod_id in self.invoice_line_ids:
            prodnum = prodnum + 1
            prod = self.env['account.move.line'].browse([prod_id[0].id])
            impuesto = self.env['account.tax'].browse([prod_id[0].tax_ids.id])
            impuestoGrupo = self.env['account.tax.group'].browse([impuesto.tax_group_id.id])
            #print('impuestoGrupo', impuestoGrupo.id)
            valorImpuesto = impuesto.amount
            IndFact = str(impuesto.x_indfact)
            if IndFact == '3':
                mntNetoIVATasaBasica = mntNetoIVATasaBasica + prod.price_subtotal
            elif IndFact == '2':
                mntNetoIvaTasaMin = mntNetoIvaTasaMin + prod.price_subtotal
            elif IndFact == '1':
                mntNoGrv = mntNoGrv + prod.price_subtotal

            for x in root.findall('./{http://cfe.dgi.gub.uy}eFact/{http://cfe.dgi.gub.uy}Detalle'):
                # print(x.tag, " ", x.text)
                newitem = ET.SubElement(x, "{http://cfe.dgi.gub.uy}Item")

                NroLinDet = str(prodnum)
                TpoCod = 'INT' + str(prodnum)
                Cod = str(prodnum) + str(prodnum) + str(prodnum)
                NomItem = str(prod.name)
                DscItem = str(prod.display_name)
                Cantidad = str(prod.quantity)
                if(prod.product_uom_id):
                    UniMed = prod.product_uom_id.name[:4]
                else:
                    UniMed = 'N/A'
                PrecioUnitario = str(prod.price_unit)
                MontoItem = str(prod.price_subtotal)

                children = ET.XML(
                    '<Item>'
                    '<NroLinDet>' + NroLinDet + '</NroLinDet>'
                                                '<CodItem>'
                                                '<TpoCod>' + TpoCod + '</TpoCod>'
                                                                      '<Cod>' + Cod + '</Cod>'
                                                                                      '</CodItem>'
                                                                                      '<IndFact>' + IndFact + '</IndFact>'
                                                                                                              '<NomItem>' + NomItem + '</NomItem>'
                                                                                                                                      '<DscItem>' + DscItem + '</DscItem>'
                                                                                                                                                              '<Cantidad>' + Cantidad + '</Cantidad>'
                                                                                                                                                                                        '<UniMed>' + UniMed + '</UniMed>'
                                                                                                                                                                                                              '<PrecioUnitario>' + PrecioUnitario + '</PrecioUnitario>'
                                                                                                                                                                                                                                                    '<MontoItem>' + MontoItem + '</MontoItem>'
                                                                                                                                                                                                                                                                                '</Item>'
                )
                newitem.extend(children)

        valorNetoIvaMin = round(mntNetoIvaTasaMin * (0.10), 3)
        valorNetoIvaBasico = round(mntNetoIVATasaBasica * (0.22), 3)

        # ## Encabezado - Totales
        for x in root.findall('./{http://cfe.dgi.gub.uy}eFact/{http://cfe.dgi.gub.uy}Encabezado'):
            # print(x.tag, " ", x.text)
            newtotal = ET.SubElement(x, "{http://cfe.dgi.gub.uy}Totales")
            totalesStr = '<Totales>'
            totalesStr = totalesStr + '<TpoMoneda>' + str(moneda.name) + '</TpoMoneda>'
            totalesStr = totalesStr + '<TpoCambio>' + str(moneda.rate) + '</TpoCambio>'
            totalesStr = totalesStr + '<MntNoGrv>' + str(mntNoGrv) + '</MntNoGrv>'
            totalesStr = totalesStr + '<MntNetoIvaTasaMin>' + str(mntNetoIvaTasaMin) + '</MntNetoIvaTasaMin>'
            totalesStr = totalesStr + '<MntNetoIVATasaBasica>' + str(round(mntNetoIVATasaBasica,3)) + '</MntNetoIVATasaBasica>'
            totalesStr = totalesStr + '<IVATasaMin>10.000</IVATasaMin>'
            totalesStr = totalesStr + '<IVATasaBasica>22.000</IVATasaBasica>'
            totalesStr = totalesStr + '<MntIVATasaMin>' + str(round(valorNetoIvaMin,3)) + '</MntIVATasaMin>'
            totalesStr = totalesStr + '<MntIVATasaBasica>' + str(round(valorNetoIvaBasico,3)) + '</MntIVATasaBasica>'

            totalesStr = totalesStr + '<MntTotal>' + str(round(self.amount_total,3)) + '</MntTotal>'
            totalesStr = totalesStr + '<CantLinDet>' + str(prodnum) + '</CantLinDet>'
            totalesStr = totalesStr + '<MntPagar>' + str(round(self.amount_total,3)) + '</MntPagar>'
            totalesStr = totalesStr + '</Totales>'

            children = ET.XML(
                totalesStr
            )
            newtotal.extend(children)

        xmlstr = ET.tostring(tree.getroot(), encoding='unicode', method='xml')
        xmlstr = xmlstr.replace("ns0:", "")
        xmlstr = xmlstr.replace("""<CFE xmlns:ns0="http://cfe.dgi.gub.uy" version="1.0">""",
                                """<?xml version="1.0" encoding="utf-8"?>
                                    <CFE xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                                    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0"
                                    xmlns="http://cfe.dgi.gub.uy">""")
        print(xmlstr)
        #self.xmlText = xmlstr
        # Coneccion WS Memory / Facturacion
        url = str(conf.url)
        client = Client(url, wsse=UsernameToken(conf.usuario, conf.clave))
        reponse = client.service.IssueCFE(
            message={'CommerceCode': conf.comercio, 'TerminalCode': conf.terminal, 'Timeout': conf.timeout,
                     'CfeType': self.tipoCFE, 'PdfRequired': 'true', 'Xml': xmlstr})
        print(reponse)
        if (reponse.RtaCode == 0 or reponse.RtaCode == 11):
            self.Uuid = str(reponse.Uuid)
            self.cfe_serieNumero = str(reponse.Series) + ' ' + str(reponse.Number)
            self.crearFe_Line(reponse, xmlstr)
            self.adjuntarPdf(reponse.Pdf)
            self.RtaCode = str(reponse.RtaCode)
            self.RtaMessage = str(reponse.RtaMessage)
            self.Series = str(reponse.Series)
            self.Number = str(reponse.Number)
            if(str(reponse.RtaCode) in ('0', '-1', '1', '3','5','11','12','30','31','89','96','99')):
                self.feEstado = str(reponse.RtaCode)
            else:
                self.feEstado = '100'
            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': ('Respuesta del Servicio'),
                    'message': "Se emite correctamente!",
                    'type': 'success',  # types: success,warning,danger,info
                    'sticky': False,  # True/False will display for few seconds if false
                },
            }
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
        else:
            mensaje = 'Error ' + str(reponse.RtaCode) + ': ' + str(reponse.RtaMessage)
            self.RtaCode = str(reponse.RtaCode)
            self.RtaMessage = str(reponse.RtaMessage)
            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': ('Respuesta del Servicio'),
                    'message': mensaje,
                    'type': 'danger',  # types: success,warning,danger,info
                    'sticky': True,  # True/False will display for few seconds if false
                },
            }

            if(reponse.RtaCode in ('0', '-1', '1', '3','5','11','12','30','31','89','96','99')):
                self.feEstado = str(reponse.RtaCode)
            else:
                self.feEstado = '100'

            raise ValidationError(mensaje)

            return notification

    def emitirCFE(self):
        # Configuracion de FE Memory
        conf = self.env['fc_pyp.settings_fc'].search([('activo', '=', 'True')])

        xmlstr = self.getXML()

        # Coneccion WS Memory / Facturacion
        url = str(conf.url)
        client = Client(url, wsse=UsernameToken(conf.usuario, conf.clave))
        tipoCFE_emitir = ''
        if (self.move_type == 'out_refund'):
            tipoCFE_emitir = self.tipoCFE_FC_NC
        else:
            tipoCFE_emitir = self.tipoCFE
        adenda = ""
        if self.narration:
            adenda = self.narration

        reponse = client.service.IssueCFE(
            message={'CommerceCode': conf.comercio, 'TerminalCode': conf.terminal, 'Timeout': conf.timeout,
                     'CfeType': tipoCFE_emitir, 'PdfRequired': 'true', 'Adenda': adenda,'Xml': xmlstr})
        print(reponse)
        if (reponse.RtaCode == 0 or reponse.RtaCode == 11):
            self.Uuid = str(reponse.Uuid)
            self.cfe_serieNumero = str(reponse.Series) + ' ' + str(reponse.Number)
            self.crearFe_Line(reponse, xmlstr)
            self.adjuntarPdf(reponse.Pdf)
            self.RtaCode = str(reponse.RtaCode)
            self.RtaMessage = str(reponse.RtaMessage)
            self.Series = str(reponse.Series)
            self.Number = str(reponse.Number)
            if (str(reponse.RtaCode) in ('0', '-1', '1', '3', '5', '11', '12', '30', '31', '89', '96', '99')):
                self.feEstado = str(reponse.RtaCode)
            else:
                self.feEstado = '100'
            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': ('Respuesta del Servicio'),
                    'message': "Se emite correctamente!",
                    'type': 'success',  # types: success,warning,danger,info
                    'sticky': False,  # True/False will display for few seconds if false
                },
            }
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
        else:
            mensaje = 'Error ' + str(reponse.RtaCode) + ': ' + str(reponse.RtaMessage)
            self.RtaCode = str(reponse.RtaCode)
            self.RtaMessage = str(reponse.RtaMessage)
            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': ('Respuesta del Servicio'),
                    'message': mensaje,
                    'type': 'danger',  # types: success,warning,danger,info
                    'sticky': True,  # True/False will display for few seconds if false
                },
            }

            if (reponse.RtaCode in ('0', '-1', '1', '3', '5', '11', '12', '30', '31', '89', '96', '99')):
                self.feEstado = str(reponse.RtaCode)
            else:
                self.feEstado = '100'

            raise ValidationError(mensaje)

            return notification



    def validateCFE(self):
        # Configuracion de FE Memory
        conf = self.env['fc_pyp.settings_fc'].search([('activo', '=', 'True')])
        # Cliente Country y State
        cliente = self.env['res.partner'].browse([self.partner_id.id])
        stateCliente = self.env['res.country.state'].browse([cliente.state_id.id])
        country = self.env['res.country'].browse([cliente.country_id.id])
        # Currency
        moneda = self.env['res.currency'].browse([self.currency_id.id])
        # Empresa
        empresa = self.env['res.company'].browse([self.env.company.id])
        # Totales
        mntNoGrv = 0
        mntNetoIvaTasaMin = 0
        mntNetoIVATasaBasica = 0

        #########
        # path = str(pathlib.Path().resolve()) + '/XML_Template'
        path = str(os.path.dirname(__file__))
        print(path)
        tree = ET.parse(os.path.join(path, 'TemplateCFE_Total.xml'))
        root = tree.getroot()
        prodnum = 0
        # XML Path
        IdDoc_Path = './{http://cfe.dgi.gub.uy}eFact/{http://cfe.dgi.gub.uy}Encabezado/{http://cfe.dgi.gub.uy}IdDoc/{http://cfe.dgi.gub.uy}'
        Emisor_Path = './{http://cfe.dgi.gub.uy}eFact/{http://cfe.dgi.gub.uy}Encabezado/{http://cfe.dgi.gub.uy}Emisor/{http://cfe.dgi.gub.uy}'
        Receptor_Path = './{http://cfe.dgi.gub.uy}eFact/{http://cfe.dgi.gub.uy}Encabezado/{http://cfe.dgi.gub.uy}Receptor/{http://cfe.dgi.gub.uy}'
        Totales_Path = './{http://cfe.dgi.gub.uy}eFact/{http://cfe.dgi.gub.uy}Encabezado/{http://cfe.dgi.gub.uy}Totales/{http://cfe.dgi.gub.uy}'

        ## Encabezado - IdDoc
        #print('Antes IF')
        if(self.move_type == 'out_refund'):
            for x in root.findall(IdDoc_Path + 'TipoCFE'):
                print('IF 1', x)
                x.text = str(self.tipoCFE_FC_NC)
            else:
                print('IF 2', x)
                for x in root.findall(IdDoc_Path + 'TipoCFE'):
                    x.text = str(self.tipoCFE)
        for x in root.findall(IdDoc_Path + 'FchEmis'):
            x.text = str(self.invoice_date)
        for x in root.findall(IdDoc_Path + 'FmaPago'):
            x.text = str(self.formaPago)
        print('despues IF')
        ## Encabezado - Emisor
        for x in root.findall(Emisor_Path + 'RUCEmisor'):
            x.text = str(empresa.vat)
        for x in root.findall(Emisor_Path + 'RznSoc'):
            x.text = str(empresa.name)
        for x in root.findall(Emisor_Path + 'CdgDGISucur'):
            x.text = str(empresa.company_registry)
        for x in root.findall(Emisor_Path + 'DomFiscal'):
            x.text = str(empresa.street)
        for x in root.findall(Emisor_Path + 'Ciudad'):
            x.text = str(empresa.city)
        for x in root.findall(Emisor_Path + 'Departamento'):
            x.text = self.env['res.country.state'].browse([cliente.state_id.id]).name

        ## Encabezado - Receptor
        for x in root.findall(Receptor_Path + 'TipoDocRecep'):
            x.text = str(cliente.x_tipoDoc)
        for x in root.findall(Receptor_Path + 'CodPaisRecep'):
            x.text = country.code
        for x in root.findall(Receptor_Path + 'DocRecep'):
            x.text = str(cliente.vat)
        for x in root.findall(Receptor_Path + 'RznSocRecep'):
            x.text = cliente.name
        for x in root.findall(Receptor_Path + 'DirRecep'):
            x.text = cliente.street
        for x in root.findall(Receptor_Path + 'CiudadRecep'):
            x.text = cliente.city

        # Items
        for prod_id in self.invoice_line_ids:
            prodnum = prodnum + 1
            prod = self.env['account.move.line'].browse([prod_id[0].id])
            impuesto = self.env['account.tax'].browse([prod_id[0].tax_ids.id])
            impuestoGrupo = self.env['account.tax.group'].browse([impuesto.tax_group_id.id])
            print('impuestoGrupo', impuestoGrupo.id)
            valorImpuesto = impuesto.amount
            IndFact = str(impuesto.x_indfact)
            if IndFact == '3':
                mntNetoIVATasaBasica = mntNetoIVATasaBasica + prod.price_subtotal
            elif IndFact == '2':
                mntNetoIvaTasaMin = mntNetoIvaTasaMin + prod.price_subtotal
            elif IndFact == '1':
                mntNoGrv = mntNoGrv + prod.price_subtotal

            for x in root.findall('./{http://cfe.dgi.gub.uy}eFact/{http://cfe.dgi.gub.uy}Detalle'):
                # print(x.tag, " ", x.text)
                newitem = ET.SubElement(x, "{http://cfe.dgi.gub.uy}Item")

                NroLinDet = str(prodnum)
                TpoCod = 'INT' + str(prodnum)
                Cod = str(prodnum) + str(prodnum) + str(prodnum)
                NomItem = str(prod.name)
                DscItem = str(prod.display_name)
                Cantidad = str(prod.quantity)
                if(prod.product_uom_id):
                    UniMed = prod.product_uom_id.name[:4]
                else:
                    UniMed = 'N/A'
                PrecioUnitario = str(prod.price_unit)
                MontoItem = str(prod.price_subtotal)

                children = ET.XML(
                    '<Item>'
                    '<NroLinDet>' + NroLinDet + '</NroLinDet>'
                                                '<CodItem>'
                                                '<TpoCod>' + TpoCod + '</TpoCod>'
                                                                      '<Cod>' + Cod + '</Cod>'
                                                                                      '</CodItem>'
                                                                                      '<IndFact>' + IndFact + '</IndFact>'
                                                                                                              '<NomItem>' + NomItem + '</NomItem>'
                                                                                                                                      '<DscItem>' + DscItem + '</DscItem>'
                                                                                                                                                              '<Cantidad>' + Cantidad + '</Cantidad>'
                                                                                                                                                                                        '<UniMed>' + UniMed + '</UniMed>'
                                                                                                                                                                                                              '<PrecioUnitario>' + PrecioUnitario + '</PrecioUnitario>'
                                                                                                                                                                                                                                                    '<MontoItem>' + MontoItem + '</MontoItem>'
                                                                                                                                                                                                                                                                                '</Item>'
                )
                newitem.extend(children)


        valorNetoIvaMin = round(mntNetoIvaTasaMin * (0.10), 3)
        valorNetoIvaBasico = round(mntNetoIVATasaBasica * (0.22), 3)


        # ## Encabezado - Totales
        for x in root.findall('./{http://cfe.dgi.gub.uy}eFact/{http://cfe.dgi.gub.uy}Encabezado'):
            # print(x.tag, " ", x.text)
            newtotal = ET.SubElement(x, "{http://cfe.dgi.gub.uy}Totales")
            totalesStr = '<Totales>'
            totalesStr = totalesStr + '<TpoMoneda>' + str(moneda.name) + '</TpoMoneda>'
            totalesStr = totalesStr + '<TpoCambio>' + str(moneda.rate) + '</TpoCambio>'
            totalesStr = totalesStr + '<MntNoGrv>' + str(mntNoGrv) +'</MntNoGrv>'
            totalesStr = totalesStr + '<MntNetoIvaTasaMin>' + str(mntNetoIvaTasaMin) + '</MntNetoIvaTasaMin>'
            totalesStr = totalesStr + '<MntNetoIVATasaBasica>' + str(round(mntNetoIVATasaBasica,3)) + '</MntNetoIVATasaBasica>'
            totalesStr = totalesStr + '<IVATasaMin>10.000</IVATasaMin>'
            totalesStr = totalesStr + '<IVATasaBasica>22.000</IVATasaBasica>'
            totalesStr = totalesStr + '<MntIVATasaMin>' + str(valorNetoIvaMin) + '</MntIVATasaMin>'
            totalesStr = totalesStr + '<MntIVATasaBasica>' + str(valorNetoIvaBasico) + '</MntIVATasaBasica>'

            totalesStr = totalesStr + '<MntTotal>' + str(self.amount_total) + '</MntTotal>'
            totalesStr = totalesStr + '<CantLinDet>' + str(prodnum) + '</CantLinDet>'
            totalesStr = totalesStr + '<MntPagar>' + str(self.amount_total) + '</MntPagar>'
            totalesStr = totalesStr + '</Totales>'

            children = ET.XML(
                totalesStr
            )
            newtotal.extend(children)

        xmlstr = ET.tostring(tree.getroot(), encoding='unicode', method='xml')
        xmlstr = xmlstr.replace("ns0:", "")
        xmlstr = xmlstr.replace("""<CFE xmlns:ns0="http://cfe.dgi.gub.uy" version="1.0">""",
                                """<?xml version="1.0" encoding="utf-8"?>
                                    <CFE xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                                    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0"
                                    xmlns="http://cfe.dgi.gub.uy">""")
        # print(xmlstr)
        #self.xmlText = xmlstr
        # Coneccion WS Memory / Facturacion
        url = str(conf.url)
        client = Client(url, wsse=UsernameToken(conf.usuario, conf.clave))
        reponse2 = client.service.ValidateCFE(
            message={'CommerceCode': conf.comercio, 'TerminalCode': conf.terminal, 'Timeout': conf.timeout, 'Xml': xmlstr})

        #newUCFE_Line = self.crearFe_Line(reponse2, xmlstr)

        if (reponse2.RtaCode == 0):
            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': ('Respuesta del Servicio'),
                    'message': "Formato de Facturación Correcta!",
                    'type': 'success',  # types: success,warning,danger,info
                    'sticky': False,  # True/False will display for few seconds if false
                },
            }
        else:
            mensaje = 'Error ' + str(reponse2.RtaCode) + ': ' + str(reponse2.RtaMessage)
            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': ('Respuesta del Servicio'),
                    'message': mensaje,
                    'type': 'danger',  # types: success,warning,danger,info
                    'sticky': True,  # True/False will display for few seconds if false
                },
            }
        return notification


    def getPDF(self):
        # Configuracion de FE Memory
        conf = self.env['fc_pyp.settings_fc'].search([('activo', '=', 'True')])
        # Coneccion WS Memory / Facturacion
        url = str(conf.url)
        client = Client(url, wsse=UsernameToken(conf.usuario, conf.clave))
        tpoCFE = str(self.tipoCFE)
        numbers = str(self.Number)
        serie = str(self.Series)
        uid = str(self.Uuid)
        reponse = client.service.GetPFD(
            message={'CommerceCode': conf.comercio, 'TerminalCode': conf.terminal, 'Timeout': conf.timeout,
                     'CfeType': tpoCFE, 'Number': numbers, 'Series': serie, 'Uuid': uid})

        if (reponse.RtaCode == 0):
            self.adjuntarPdf(reponse.Pdf)
            # self.action_get_attachment()
            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': ('Respuesta del Servicio'),
                    'message': "PDF Obtenido correctamente!",
                    'type': 'success',  # types: success,warning,danger,info
                    'sticky': False,  # True/False will display for few seconds if false
                },
            }
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
        else:
            mensaje = 'Error ' + str(reponse.RtaCode) + ': ' + str(reponse.RtaMessage)
            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': ('Respuesta del Servicio'),
                    'message': mensaje,
                    'type': 'danger',  # types: success,warning,danger,info
                    'sticky': True,  # True/False will display for few seconds if false
                },
            }
            return notification

    def crearFe_Line(self, reponse2, xmlstr):
        print('xml', reponse2.Pdf)
        b64_pdf = base64.b64encode(reponse2.Pdf)
        name = self.name
        attach = {
            'name': name,
            'type': 'binary',
            'datas': b64_pdf,
            # 'datas_fname': name + '.pdf',
            'store_fname': name,
            # 'res_model': self._name,
            # 'res_id': self.id,
            'mimetype': 'application/pdf'
        }
        pdf_atach = self.env['ir.attachment'].create(attach)

        #print('xml ATACH')
        #Crear Linea de UCFE
        ucfe_line = {
            'display_name': str(reponse2.Number),
            'Number': str(reponse2.Number),
            'Series': str(reponse2.Series),
            'RtaMessage': str(reponse2.RtaMessage),
            'RtaCode': str(reponse2.RtaCode),
            'Uuid': str(reponse2.Uuid),
            'xmlText': xmlstr,
            'cfe_id': self.id,
            'line_attachment_id': pdf_atach.id
        }
        linea = self.env['fc_pyp.fe_line'].create(ucfe_line)
        return linea

    def crearPDF_attachment(self, pdf):
        #pdf = b'010001010111001001110010011011110111001000100000011000010110110000100000011100010111010101100101011100100110010101110010001000000110111101100010011101000110010101101110011001010111001000100000011011110010000001100011011011110110111001110110011001010111001001110100011010010111001000100000010100000100010001000110001000000110010001100101001000000101010101000011010001100100010100100000'
        # b64_pdf = pdf
        b64_pdf = base64.b64encode(pdf)
        name = self.cfe_serieNumero + ' - '+ self.name
        attach = {
            'name': name,
            'type': 'binary',
            'datas': b64_pdf,
            #'datas_fname': name + '.pdf',
            'store_fname': name,
            # 'res_model': self._name,
            # 'res_id': self.id,
            'mimetype': 'application/pdf'
        }
        return self.env['ir.attachment'].create(attach)


    def camposObligatorios(self):
        mensaje = ''
        if(self.move_type == 'out_refund' and self.tipoCFE_FC_NC == False): mensaje = mensaje + '- Tipo Comp. NC \n'
        if (self.tipoDoc == False): mensaje = mensaje + '- Cliente / Tipo Documento \n'
        if (self.customerRUT == False): mensaje = mensaje + '- Cliente / Documento \n'
        cliente = self.env['res.partner'].browse([self.partner_id.id])
        if (cliente.country_id.id  == False): mensaje = mensaje + '- Cliente / País \n'
        if (self.formaPago == False): mensaje = mensaje + '- Forma de pago\n'
        if (self.invoice_date == ''): mensaje = mensaje + '- Fecha de Factura\n'
        return mensaje

    def actulizarEstadoUCFE(self):
        # Configuracion de FE Memory
        conf = self.env['fc_pyp.settings_fc'].search([('activo', '=', 'True')])
        url = str(conf.url)
        client = Client(url, wsse=UsernameToken(conf.usuario, conf.clave))
        tipoCFE = ''
        Number = self.Number
        Series = self.Series
        Uuid = self.Uuid
        tipoCFE_Validar = ''
        if(self.tipoCFE_FC_NC != False):
            tipoCFE = self.tipoCFE_FC_NC
        elif(self.tipoCFE != False):
            tipoCFE = self.tipoCFE

        if(tipoCFE != '' and tipoCFE != False and Number != False and Series != False and Uuid != False):
            reponse = client.service.CheckCFEState(
                message={'CommerceCode': conf.comercio, 'TerminalCode': conf.terminal, 'Timeout': conf.timeout,
                         'CfeType': tipoCFE, 'Number': Number, 'Series': Series, 'Uuid': Uuid})
            RtaCodeDevuelto = str(reponse.RtaCode)
            if(RtaCodeDevuelto != self.feEstado):
                self.write({
                    'feEstado': RtaCodeDevuelto
                })

    def actulizarMasivoEstadoUCFE(self):
        invoices_ids = self.env['account.move'].browse(self.env.context.get('active_ids'))
        try:
            for inv in invoices_ids:
                inv.actulizarEstadoUCFE()
        except Exception as e:
            raise print('Error: /n' + str(e))


    def actulizarMasivoEstadoUCFE_Scheduler(self):
        invoices_ids = self.env['account.move'].search([('feEstado', '=', '11')])
        print(invoices_ids)
        try:
             for inv in invoices_ids:
                 inv.actulizarEstadoUCFE()
        except Exception as e:
             raise ValidationError('Error: /n' + str(e))


    def getXML(self):
        # Cliente Country y State
        cliente = self.env['res.partner'].browse([self.partner_id.id])
        stateCliente = self.env['res.country.state'].browse([cliente.state_id.id])
        country = self.env['res.country'].browse([cliente.country_id.id])

        # Currency
        moneda = self.env['res.currency'].browse([self.currency_id.id])
        TpoMoneda = str(moneda.name)
        TpoCambio = str(round(1/moneda.rate,3))
        if(moneda.date != False):
            if (self.date < moneda.date):
                ## hay que buscar la fecha correspondiente
                tasa = self.env['res.currency.rate'].search(
                    ['&', ('currency_id', '=', self.currency_id.id), ('name', '<', str(self.date))], limit=1)
                TpoCambio = str(round(1/tasa.rate,3))
        print(str(TpoCambio))
        # Empresa
        empresa = self.env['res.company'].browse([self.env.company.id])

        # Totales
        mntNoGrv = 0
        mntNetoIvaTasaMin = 0
        mntNetoIVATasaBasica = 0

        #########
        #path = str(pathlib.Path().resolve()) + '/XML_Template'
        path = str(os.path.dirname(__file__))
        tree = ET.parse(os.path.join(path, 'TemplateCFE_Total.xml'))
        root = tree.getroot()
        prodnum = 0
        # XML Path
        IdDoc_Path = './{http://cfe.dgi.gub.uy}eFact/{http://cfe.dgi.gub.uy}Encabezado/{http://cfe.dgi.gub.uy}IdDoc/{http://cfe.dgi.gub.uy}'
        Emisor_Path = './{http://cfe.dgi.gub.uy}eFact/{http://cfe.dgi.gub.uy}Encabezado/{http://cfe.dgi.gub.uy}Emisor/{http://cfe.dgi.gub.uy}'
        Receptor_Path = './{http://cfe.dgi.gub.uy}eFact/{http://cfe.dgi.gub.uy}Encabezado/{http://cfe.dgi.gub.uy}Receptor/{http://cfe.dgi.gub.uy}'
        Totales_Path = './{http://cfe.dgi.gub.uy}eFact/{http://cfe.dgi.gub.uy}Encabezado/{http://cfe.dgi.gub.uy}Totales/{http://cfe.dgi.gub.uy}'

        ## Encabezado - IdDoc
        if(self.move_type == 'out_refund'):
            for x in root.findall(IdDoc_Path + 'TipoCFE'):
                x.text = str(self.tipoCFE_FC_NC)
        else:
            for x in root.findall(IdDoc_Path + 'TipoCFE'):
                x.text = str(self.tipoCFE)
        for x in root.findall(IdDoc_Path + 'FchEmis'):
            x.text = str(self.invoice_date)
        for x in root.findall(IdDoc_Path + 'FmaPago'):
            x.text = str(self.formaPago)

        ## Encabezado - Emisor
        for x in root.findall(Emisor_Path + 'RUCEmisor'):
            x.text = str(empresa.vat)
        for x in root.findall(Emisor_Path + 'RznSoc'):
            x.text = str(empresa.name)
        for x in root.findall(Emisor_Path + 'CdgDGISucur'):
            x.text = str(empresa.company_registry)
        for x in root.findall(Emisor_Path + 'DomFiscal'):
            x.text = str(empresa.street)
        for x in root.findall(Emisor_Path + 'Ciudad'):
            x.text = str(empresa.city)
        for x in root.findall(Emisor_Path + 'Departamento'):
            x.text = self.env['res.country.state'].browse([cliente.state_id.id]).name

        ## Encabezado - Receptor
        for x in root.findall(Receptor_Path + 'TipoDocRecep'):
            x.text = str(cliente.x_tipoDoc)
        for x in root.findall(Receptor_Path + 'CodPaisRecep'):
            x.text = country.code
        for x in root.findall(Receptor_Path + 'DocRecep'):
            x.text = str(cliente.vat)
        for x in root.findall(Receptor_Path + 'RznSocRecep'):
            x.text = cliente.name
        for x in root.findall(Receptor_Path + 'DirRecep'):
            x.text = cliente.street
        for x in root.findall(Receptor_Path + 'CiudadRecep'):
            x.text = cliente.city

        # Items
        for prod_id in self.invoice_line_ids:
            prodnum = prodnum + 1
            prod = self.env['account.move.line'].browse([prod_id[0].id])
            impuesto = self.env['account.tax'].browse([prod_id[0].tax_ids.id])
            impuestoGrupo = self.env['account.tax.group'].browse([impuesto.tax_group_id.id])
            #print('impuestoGrupo', impuestoGrupo.id)
            valorImpuesto = impuesto.amount
            MontoNF = ''
            IndFact = str(impuesto.x_indfact)
            if IndFact == '3':
                mntNetoIVATasaBasica = mntNetoIVATasaBasica + prod.price_subtotal
            elif IndFact == '2':
                mntNetoIvaTasaMin = mntNetoIvaTasaMin + prod.price_subtotal
            elif IndFact == '1':
                mntNoGrv = mntNoGrv + prod.price_subtotal
            elif IndFact == '67':
                MontoNF = str(prod.price_subtotal)
                if '-' not in str(prod.price_unit):
                    IndFact = '6'
                else:
                    IndFact = '7'

            for x in root.findall('./{http://cfe.dgi.gub.uy}eFact/{http://cfe.dgi.gub.uy}Detalle'):
                # print(x.tag, " ", x.text)
                newitem = ET.SubElement(x, "{http://cfe.dgi.gub.uy}Item")

                NroLinDet = str(prodnum)
                TpoCod = 'INT' + str(prodnum)
                Cod = str(prodnum) + str(prodnum) + str(prodnum)
                NomItem = str(prod.product_id.name) #str(prod.name)
                DscItem = str(prod.name) #str(prod.display_name)
                Cantidad = str(prod.quantity)
                if(prod.product_uom_id):
                    UniMed = prod.product_uom_id.name[:4]
                else:
                    UniMed = 'N/A'
                PrecioUnitario = str(abs(prod.price_unit))
                MontoItem = str(abs(prod.price_subtotal))

                children = ET.XML(
                    '<Item>'
                    '<NroLinDet>' + NroLinDet + '</NroLinDet>'
                                                '<CodItem>'
                                                '<TpoCod>' + TpoCod + '</TpoCod>'
                                                                      '<Cod>' + Cod + '</Cod>'
                                                                                      '</CodItem>'
                                                                                      '<IndFact>' + IndFact + '</IndFact>'
                                                                                                              '<NomItem>' + NomItem + '</NomItem>'
                                                                                                                                      '<DscItem>' + DscItem + '</DscItem>'
                                                                                                                                                              '<Cantidad>' + Cantidad + '</Cantidad>'
                                                                                                                                                                                        '<UniMed>' + UniMed + '</UniMed>'
                                                                                                                                                                                                              '<PrecioUnitario>' + PrecioUnitario + '</PrecioUnitario>'
                                                                                                                                                                                                                                                    '<MontoItem>' + MontoItem + '</MontoItem>'
                                                                                                                                                                                                                                                                                '</Item>'
                )
                newitem.extend(children)

        valorNetoIvaMin = round(mntNetoIvaTasaMin * (0.10), 2)
        valorNetoIvaBasico = round(mntNetoIVATasaBasica * (0.22), 2)

        # ## Encabezado - Totales
        for x in root.findall('./{http://cfe.dgi.gub.uy}eFact/{http://cfe.dgi.gub.uy}Encabezado'):
            # print(x.tag, " ", x.text)
            newtotal = ET.SubElement(x, "{http://cfe.dgi.gub.uy}Totales")
            totalesStr = '<Totales>'
            totalesStr = totalesStr + '<TpoMoneda>' + str(TpoMoneda) + '</TpoMoneda>'
            totalesStr = totalesStr + '<TpoCambio>' + str(TpoCambio) + '</TpoCambio>'
            totalesStr = totalesStr + '<MntNoGrv>' + str(mntNoGrv) + '</MntNoGrv>'
            totalesStr = totalesStr + '<MntNetoIvaTasaMin>' + str(mntNetoIvaTasaMin) + '</MntNetoIvaTasaMin>'
            totalesStr = totalesStr + '<MntNetoIVATasaBasica>' + str(round(mntNetoIVATasaBasica,3)) + '</MntNetoIVATasaBasica>'
            totalesStr = totalesStr + '<IVATasaMin>10.000</IVATasaMin>'
            totalesStr = totalesStr + '<IVATasaBasica>22.000</IVATasaBasica>'
            totalesStr = totalesStr + '<MntIVATasaMin>' + str(round(valorNetoIvaMin,2)) + '</MntIVATasaMin>'
            totalesStr = totalesStr + '<MntIVATasaBasica>' + str(round(valorNetoIvaBasico,2)) + '</MntIVATasaBasica>'
            if MontoNF != '':
                totalesStr = totalesStr + '<MntTotal>' + str(round(self.amount_total - float(MontoNF),2)) + '</MntTotal>'
            else:
                totalesStr = totalesStr + '<MntTotal>' + str(round(self.amount_total, 2)) + '</MntTotal>'
            totalesStr = totalesStr + '<CantLinDet>' + str(prodnum) + '</CantLinDet>'
            if MontoNF != '':
                totalesStr = totalesStr + '<MontoNF>' + MontoNF + '</MontoNF>'
            totalesStr = totalesStr + '<MntPagar>' + str(round(self.amount_total, 2)) + '</MntPagar>'
            totalesStr = totalesStr + '</Totales>'

            children = ET.XML(
                totalesStr
            )
            newtotal.extend(children)

        if (self.move_type == 'out_refund'):
            for x in root.findall('./{http://cfe.dgi.gub.uy}eFact'):
                print(x.tag, " ", x.text)
                newref = ET.SubElement(x, "{http://cfe.dgi.gub.uy}Referencia")
                totalesStr = '<Referencia>'
                totalesStr = totalesStr +'<Referencia>'
                totalesStr = totalesStr + '<NroLinRef>' + str(1) + '</NroLinRef>'
                totalesStr = totalesStr + '<IndGlobal>' + str(1) + '</IndGlobal>'
                totalesStr = totalesStr + '<RazonRef>' + str(self.cfe_serieNumero)+ '</RazonRef>'
                totalesStr = totalesStr + '<FechaCFEref>' + str(self.invoice_date) + '</FechaCFEref>'
                totalesStr = totalesStr + '</Referencia>'
                totalesStr = totalesStr + '</Referencia>'
            childrenRef = ET.XML(
                totalesStr
            )
            newref.extend(childrenRef)

        xmlstr = ET.tostring(tree.getroot(), encoding='unicode', method='xml')
        xmlstr = xmlstr.replace("ns0:", "")
        xmlstr = xmlstr.replace("""<CFE xmlns:ns0="http://cfe.dgi.gub.uy" version="1.0">""",
                                """<?xml version="1.0" encoding="utf-8"?>
                                    <CFE xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                                    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0"
                                    xmlns="http://cfe.dgi.gub.uy">""")

        print(xmlstr)
        return xmlstr

    def adjuntarPdf(self, pdf):
        b64_pdf = base64.b64encode(pdf)
        name = self.name
        return self.env['ir.attachment'].create({
            'name': name,
            'type': 'binary',
            'datas': b64_pdf,
            #'datas_fname': name + '.pdf',
            'store_fname': name,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf'
        })


    def button_draft(self):
        res = super(fe_UCFE, self).button_draft()
        print('button_draft')
        if(self.tipoCFE != False or self.tipoCFE_FC_NC != False):
            raise ValidationError('No es posible restablecer a borrador un Documento Electrónico')
        return res

    # @api.onchange('currency_id')
    # def _onchange_currency_id(self):
    #     if(self.line_ids != False):
    #         print(len(self.line_ids))
    #         for acc_id in self.line_ids:
    #             account_line = self.env['account.move.line'].browse([acc_id[0].id])
    #             account_acount = self.env['account.account'].browse([account_line.account_id.id])
    #             print(account_acount.currency_id.id)
    #             print(self.currency_id.id)
    #             if(account_acount.currency_id.id != False and account_acount.currency_id.id != self.currency_id.id):
    #                 self.x_account_currency = True
    #                 break
    #             else:
    #                 self.x_account_currency = False

    # def write(self, values):
    #     val = self.validarCurrency()
    #     if (val == True):
    #         mensaje = self.mensajeValidarCuerrency()
    #         raise ValidationError(mensaje)
    #     # print(values)
    #     # print('line_ids *** ', values['line_ids'])
    #     # for acc_id in values['line_ids']:
    #     #     print('acc_id **', acc_id)
    #     #     print('acc_id[account_id] ', acc_id['account_id'])
    #     #
    #     # if 'currency_id' in values.keys():
    #     #     print('En currency', values)
    #     #     print('line_ids *** ', values['line_ids'])
    #     #     for acc_id in values['line_ids']:
    #     #         print('acc_id ', acc_id)
    #     #         account_line = self.env['account.move.line'].browse([acc_id[0].id])
    #     #         account_acount = self.env['account.account'].browse([account_line.account_id.id])
    #     #         print(account_acount.currency_id.id)
    #     #         if(values['currency_id'] == 2 and (account_acount.currency_id.id == False or account_acount.currency_id.id == 46)):
    #     #             mensaje = self.mensajeValidarCuerrency()
    #     #             raise ValidationError(mensaje)
    #     #         elif(values['currency_id'] == 46 and (account_acount.currency_id.id != False or account_acount.currency_id.id != 46)):
    #     #             mensaje = self.mensajeValidarCuerrency()
    #     #             raise ValidationError(mensaje)
    #     #         #if (account_acount.currency_id.id != False and account_acount.currency_id.id != values['currency_id']):
    #     #             # mensaje = self.mensajeValidarCuerrency()
    #     #             # raise ValidationError(mensaje)
    #     # elif(val == True):
    #     #     mensaje = self.mensajeValidarCuerrency()
    #     #     raise ValidationError(mensaje)
    #     # if 'x_account_currency' in values.keys():
    #     #     print("value is ...", values['x_account_currency'])
    #     #     if(values['x_account_currency'] == True):
    #     #         raise ValidationError('Los Apuntes Contables deben ser de la misma Moneda que la Factura!')
    #
    #     res = super(fe_UCFE, self).write(values)
    #     return res

    def validarCurrency(self):
        val = False
        print(self.line_ids)
        if(self.line_ids != False):
            for acc_id in self.line_ids:
                account_line = self.env['account.move.line'].browse([acc_id[0].id])
                account_acount = self.env['account.account'].browse([account_line.account_id.id])
                print(account_acount.user_type_id.name)
                print(account_acount.user_type_id.id)
                if (account_acount.user_type_id.id == 1 or account_acount.user_type_id.id == 2):
                    print('account_acount.currency_id.id', account_acount.currency_id.id)
                    print('self.currency_id.id', self.currency_id.id)
                    print('account_acount.user_type_id.id', account_acount.user_type_id.id)
                    if(self.currency_id.id == 2 and (account_acount.currency_id.id == False or account_acount.currency_id.id == 46)):
                        val = True
                        break
                    elif(self.currency_id.id == 46 and (account_acount.currency_id.id != False or account_acount.currency_id.id == 2)):
                        val = True
        return val

    def mensajeValidarCuerrency(self):
        mensaje = 'Atención: Para realizar una factura en esta moneada, cambie la cuenta deudora/acreedora por una cuenta en la misma moneda'
        print(self.currency_id)
        if(self.currency_id != False):
            mensaje = 'Atención: Para realizar una factura en '+ self.currency_id.name + ', cambie la cuenta deudora/acreedora por una cuenta en ' + self.currency_id.currency_unit_label
        return mensaje
    # def write(self, values):
    #     if(self.x_account != False and (self.x_account_ant == False or self.x_account_ant == '')):
    #         for acc_id in self.line_ids:
    #             account_line = self.env['account.move.line'].browse([acc_id[0].id])
    #             account_acount = self.env['account.account'].browse([account_line.account_id.id])
    #             if(account_acount.user_type_id.id == 1):
    #                 #self.x_account_ant = account_line.account_id.id
    #                 #values.update({'x_account_ant' : account_line.account_id.id})
    #                 values.update({'x_account_ant': 6})
    #                 account_line.write({'account_id': self.x_account.id})
    #                 #account_line.account_id = self.x_account.id
    #     res = super(fe_UCFE, self).write(values)
    #     #actualizarCuentas(self)
    #     return res


    # @api.onchange('currency_id')
    # def _onchange_currency_id(self):
    #     if self.currency_id.id == 2:
    #         self.x_account_hide = True
    #         self.x_account = False
    #     else:
    #         self.x_account_hide = False
    #         print(self.x_account_ant)
    #         if(self.x_account_ant != False):
    #                 for acc_id in self.line_ids:
    #                     account_line = self.env['account.move.line'].browse([acc_id[0].id])
    #                     account_acount = self.env['account.account'].browse([account_line.account_id.id])
    #                     if(account_acount.user_type_id.id == 1):
    #                         print('self.x_account_ant', self.x_account_ant)
    #                         account_line.account_id = int(self.x_account_ant)
    #                         print(account_line.account_id)
    #                         #self.account_line.account_id = self.env['account.account'].browse([int(self.x_account_ant)]).id
    #                         self.x_account_ant = False



    # @api.onchange('x_account')
    # def _onchange_x_account(self):
    #     print(self.x_account.id)
    #     for acc_id in self.line_ids:
    #         account_line = self.env['account.move.line'].browse([acc_id[0].id])
    #         account_acount = self.env['account.account'].browse([account_line.account_id.id])
    #         if(account_acount.user_type_id.id == 1):
    #             print('account_line.account_id.id',account_line.account_id.id)
    #             if(self.x_account_ant == False):
    #                 #self.x_account_ant = account_line.account_id.id
    #                 self.x_account_ant = 6
    #             account_line.account_id = self.x_account.id



    # @api.onchange('invoice_line_ids')
    # def _onchange_invoice_line_ids(self):
    #     print('invoice_line_ids', self.x_account.id)
    #     if(self.x_account != False and self.x_account_ant == False):
    #         for acc_id in self.line_ids:
    #             account_line = self.env['account.move.line'].browse([acc_id[0].id])
    #             account_acount = self.env['account.account'].browse([account_line.account_id.id])
    #             if(account_acount.user_type_id.id == 1):
    #                 #self.x_account_ant = account_line.account_id.id
    #                 self.x_account_ant = 6
    #                 account_line.account_id = self.x_account.id