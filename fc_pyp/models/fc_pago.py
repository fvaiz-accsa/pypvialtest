from odoo import models, fields, api
from zeep import Client
from zeep.wsse.username import UsernameToken
import xml.etree.ElementTree as ET
import pathlib
import os
import base64
from odoo.exceptions import ValidationError
from datetime import datetime


class fc_pago(models.Model):
    _inherit = 'account.payment'

    tipoCFE_pay = fields.Selection([('182', 'e-Resguardo')], string='Tipo Comprobante')
    # info = fields.Text(string='Info')
    customerRUT_pay = fields.Char(string='Documento', related='partner_id.vat')
    tipoDoc_pay = fields.Selection(string='Tipo Doc.', related='partner_id.x_tipoDoc')

    Number_pay = fields.Char(string='Number')
    RtaMessage_pay = fields.Char(string='RtaMessage')
    RtaCode_pay = fields.Char(string='RtaCode')
    Series_pay = fields.Char(string='Series')
    Uuid_pay = fields.Char(string='Identificador')
    xmlText_pay = fields.Text(string='XML')
    feEstado_pay = fields.Selection([('0', 'VALIDA'), ('-1', 'Error en el servidor'), ('1', 'Denegado'),
                                 ('3', 'Comercio inválido'), ('5', 'CFE rechazado por DGI'), ('11', 'Enviada'),
                                 ('12', 'Requerimiento inválido'),('30', 'Error en formato'),('31', 'Error en formato de CFE'),
                                 ('89', 'Terminal inválida'),('96', 'Error en sistema'),('99', 'Sesión no iniciada'),
                                 ('100', 'Error Desconocido')],
                                string='Estado DGI')
    retenciones = fields.Many2one(string='Retenciones', comodel_name='fc_pyp.fc_codigos')

    cfe_emitidas_pay = fields.One2many('fc_pyp.fe_line', 'pay_id', 'Doc. Electrónico' )
    cfe_serieNumero_pay = fields.Text(string='Numero')

    ## Para Imprimir Comprobante
    descripcion = fields.Text(string='Descripción')
    observaciones = fields.Text(string='Observaciones')

    ### CHEQUES / PAGOS ###
    referenciaPago = fields.Char(string='Referencia')
    fechaEmisionPago = fields.Date(string='Fecha Emisión ')
    fechaVencimientoPago = fields.Date(string='Fecha Vencimiento')
    isChequePago = fields.Boolean(string='Es Cheque')
    bancoPago_id = fields.Many2one('res.bank', string='Banco')
    estadoChequePago = fields.Selection([('0', 'Por Cobrar'), ('1', 'Cobrado'), ('2', 'Rechazado '),
                                     ('3', 'Anulado')], string='Estado Cheque')
    list_cheques_id = fields.One2many('fc_pyp.fc_pago_cheque', 'cheq_id', 'Cheques')

    codigo_pay = fields.Char(string='Código')

    #amount_total = fields.Monetary(string='Total')

    #Cheque
    @api.onchange('list_cheques_id')
    def _onchangelist_cheques_id(self):
        valorTotal = 0
        for cheq in self.list_cheques_id:
            print('Valor', self.env['fc_pyp.fc_pago_cheque'].browse([cheq.id]).valor)
            valorTotal += self.env['fc_pyp.fc_pago_cheque'].browse([cheq.id]).valor
        print('onchange_list_cheques_id',str(self.list_cheques_id))
        self.amount = valorTotal

    # @api.model
    def action_post(self):
        print(self._context.get('ischeque_wiz'))
        res = super(fc_pago, self).action_post()

        #print("Context", self._context.get())
        tipoCFE_wiz = self._context.get('tipoCFE_wiz')
        # Cheques
        ischeque_wiz = self._context.get('ischeque_wiz')
        referenciaCheque = self._context.get('referenciaCheque')
        fechaEmisionCheque = self._context.get('fechaEmisionCheque')
        fechaFencimientoCheque = self._context.get('fechaFencimientoCheque')
        estadoCheque = self._context.get('estadoCheque')
        banco_idCheque = self._context.get('banco_idCheque')
        print('ischeque_wiz:', ischeque_wiz)
        if (referenciaCheque != False):
            self.referenciaPago = referenciaCheque
        if (fechaEmisionCheque != False):
            self.fechaEmisionPago = fechaEmisionCheque
        if (fechaFencimientoCheque != False):
            self.fechaVencimientoPago = fechaFencimientoCheque
        if (estadoCheque != False):
            self.estadoChequePago = estadoCheque
        if (banco_idCheque != False):
            self.bancoPago_id = banco_idCheque
        if (str(ischeque_wiz) != 'None' and ischeque_wiz != False):  # and self.list_cheques_id == False):
            self.isChequePago = ischeque_wiz
            # Crear Linea de Cheque
            vals = {
                'referenciaPago': referenciaCheque,
                'fechaEmisionPago': fechaEmisionCheque,
                'fechaVencimientoPago': fechaFencimientoCheque,
                'bancoPago_id': banco_idCheque.id,
                'cheq_id': self.id,
                'valor': self.amount
            }
            self.env['fc_pyp.fc_pago_cheque'].create(vals)
        # raise ValidationError('action_post')
        try:
            if (self.tipoCFE_pay != False):
                mensaje = self.camposObligatorios()
                if (mensaje != ''):
                    raise ValidationError('No se puede Confirmar, los siguientes campos son obligatorios: \n' + mensaje)
                val = {'tipoCFE_wiz': 'No'}
                self.emitirCFE(val, '0')
            elif (tipoCFE_wiz == '182'):
                val = {'tipoCFE_wiz': 'No'}
                self.emitirCFE(val, '0')
        except Exception as e:
            raise ValidationError('Error: ' + str(e))
        else:
            return res

    #@api.model
    def action_draft(self):
        res = super(fc_pago, self).action_draft()
        #raise ValidationError('action_post')
        try:
            if (self.Uuid_pay != False):
                raise ValidationError('No es posible restablecer a borrador un Documento Electrónico')
                return res
        except Exception as e:
            raise ValidationError('Error: ' + str(e))
        else:
            return res
    #Cheque
    @api.onchange('journal_id')
    def _onchangeJournal(self):
        self.isChequePago = self.journal_id.cheques
        print('onchange',str(self.isChequePago))


    def write(self, values):
        if('isChequePago' in values.keys()):
            if(values['isChequePago'] == False):
                self.referenciaPago = False
                self.estadoChequePago = False
                self.fechaVencimientoPago = False
                self.fechaEmisionPago = False
                self.bancoPago_id = False
        res = super(fc_pago, self).write(values)
        return res

    def camposObligatorios(self):
        mensaje = ''
        if (self.tipoDoc_pay == False): mensaje = mensaje + '- Cliente / Tipo Documento \n'
        if (self.customerRUT_pay == False): mensaje = mensaje + '- Cliente / Documento \n'
        cliente = self.env['res.partner'].browse([self.partner_id.id])
        if (cliente.country_id.id  == False): mensaje = mensaje + '- Cliente / País \n'
        if (self.date == ''): mensaje = mensaje + '- Fecha de Factura\n'
        return mensaje

    def getXML(self, values):
        tipoCFE_wiz = self._context.get('tipoCFE_wiz')
        cliente_id = ''
        currency_id= ''
        tipo_cfe = ''
        pyament_date = ''
        amount = ''
        RazonRef = ''
        if(tipoCFE_wiz == '182'):
            cliente_id = self._context.get('cliente_id')
            currency_id = self._context.get('currency_id_wiz')
            tipo_cfe = self._context.get('tipoCFE_wiz')
            pyament_date = self._context.get('payment_date_wiz')
            amount =  self._context.get('amount_wiz')
            RazonRef =  self._context.get('communication')
        else:
            cliente_id = self.partner_id.id  #values.get('partner_id')
            currency_id = self.currency_id.id #values.get('currency_id')
            tipo_cfe = self.tipoCFE_pay #values.get('tipoCFE_pay')
            pyament_date = self.date #values.get('date')
            amount = self.amount #values.get('amount')
            RazonRef = self.name #values.get('name')

        #CodRet = '1246193'
        CodRet = self.retenciones.codigo
        MntSujetoaRet = str(amount)
        ValRetPerc = str(amount)

        # Cliente Country y State
        cliente = self.env['res.partner'].browse([cliente_id])
        stateCliente = self.env['res.country.state'].browse([cliente.state_id.id])
        country = self.env['res.country'].browse([cliente.country_id.id])

        # Currency
        moneda = self.env['res.currency'].browse([currency_id])
        TpoMoneda = str(moneda.name)
        TpoCambio = str(moneda.rate)
        if(moneda.date != False):
            if (pyament_date < moneda.date):
                ## hay que buscar la fecha correspondiente
                tasa = self.env['res.currency.rate'].search(
                    ['&', ('currency_id', '=', currency_id), ('name', '<', str(pyament_date))], limit=1)
                TpoCambio = str(tasa.rate)

        # Empresa
        empresa = self.env['res.company'].browse([self.env.company.id])

        #########
        #path = str(pathlib.Path().resolve()) + '/XML_Template'
        path = str(os.path.dirname(__file__))
        tree = ET.parse(os.path.join(path, 'TemplateCFE_Resguardo.xml'))
        root = tree.getroot()
        prodnum = 0
        # XML Path
        IdDoc_Path = './{http://cfe.dgi.gub.uy}eResg/{http://cfe.dgi.gub.uy}Encabezado/{http://cfe.dgi.gub.uy}IdDoc/{http://cfe.dgi.gub.uy}'
        Emisor_Path = './{http://cfe.dgi.gub.uy}eResg/{http://cfe.dgi.gub.uy}Encabezado/{http://cfe.dgi.gub.uy}Emisor/{http://cfe.dgi.gub.uy}'
        Receptor_Path = './{http://cfe.dgi.gub.uy}eResg/{http://cfe.dgi.gub.uy}Encabezado/{http://cfe.dgi.gub.uy}Receptor/{http://cfe.dgi.gub.uy}'
        Totales_Path = './{http://cfe.dgi.gub.uy}eResg/{http://cfe.dgi.gub.uy}Encabezado/{http://cfe.dgi.gub.uy}Totales/{http://cfe.dgi.gub.uy}'

        ## Encabezado - IdDoc

        for x in root.findall(IdDoc_Path + 'TipoCFE'):
            x.text = str(tipo_cfe)
        for x in root.findall(IdDoc_Path + 'FchEmis'):
            x.text = str(pyament_date)

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

        for x in root.findall('./{http://cfe.dgi.gub.uy}eResg/{http://cfe.dgi.gub.uy}Detalle'):

            newitem = ET.SubElement(x, "{http://cfe.dgi.gub.uy}Item")

            children = ET.XML(
                '<Item>'
                '<NroLinDet>1</NroLinDet>'
                '<RetencPercep>'
                   '<CodRet>' + CodRet + '</CodRet>'
                       '<MntSujetoaRet>' + MntSujetoaRet + '</MntSujetoaRet>'
                       '<ValRetPerc>' + ValRetPerc + '</ValRetPerc>'
                  '</RetencPercep>'
                   '</Item>'
            )
            newitem.extend(children)

        # ## Encabezado - Totales
        for x in root.findall('./{http://cfe.dgi.gub.uy}eResg/{http://cfe.dgi.gub.uy}Encabezado'):
            # print(x.tag, " ", x.text)
            newtotal = ET.SubElement(x, "{http://cfe.dgi.gub.uy}Totales")
            totalesStr = '<Totales>'
            totalesStr = totalesStr + '<TpoMoneda>' + str(TpoMoneda) + '</TpoMoneda>'
            totalesStr = totalesStr + '<TpoCambio>' + str(TpoCambio) + '</TpoCambio>'
            totalesStr = totalesStr + '<MntTotRetenido>' + str(MntSujetoaRet) + '</MntTotRetenido>'
            totalesStr = totalesStr + '<CantLinDet>1</CantLinDet>'
            totalesStr = totalesStr + '<RetencPercep>'
            totalesStr = totalesStr + '<CodRet>' + CodRet + '</CodRet>'
            totalesStr = totalesStr + '<ValRetPerc>' + MntSujetoaRet + '</ValRetPerc>'
            totalesStr = totalesStr + '</RetencPercep>'
            totalesStr = totalesStr + '</Totales>'

            children = ET.XML(
                totalesStr
            )
            newtotal.extend(children)


        for x in root.findall('./{http://cfe.dgi.gub.uy}eResg'):
            print(x.tag, " ", x.text)
            newref = ET.SubElement(x, "{http://cfe.dgi.gub.uy}Referencia")
            totalesStr = '<Referencia>'
            totalesStr = totalesStr +'<Referencia>'
            totalesStr = totalesStr + '<NroLinRef>' + str(1) + '</NroLinRef>'
            totalesStr = totalesStr + '<IndGlobal>' + str(1) + '</IndGlobal>'
            totalesStr = totalesStr + '<RazonRef>' + str(RazonRef) + '</RazonRef>'
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


    def emitirCFE(self, valores, res_id):
        # Configuracion de FE Memory
        conf = self.env['fc_pyp.settings_fc'].search([('activo', '=', 'True')])

        xmlstr = self.getXML(valores)
        pago_id = ''
        pago_obj = ''
        if(res_id == '0'):
            pago_id = self.id
            pago_obj = self
        else:
            pago_id = res_id
            pago_obj = self.env['account.payment'].browse([pago_id])

        # Coneccion WS Memory / Facturacion
        url = str(conf.url)
        client = Client(url, wsse=UsernameToken(conf.usuario, conf.clave))

        reponse = client.service.IssueCFE(
            message={'CommerceCode': conf.comercio, 'TerminalCode': conf.terminal, 'Timeout': conf.timeout,
                     'CfeType': '182', 'PdfRequired': 'true', 'Xml': xmlstr.strip()})

        if (reponse.RtaCode == 0 or reponse.RtaCode == 11):
            pago_obj.Uuid_pay = str(reponse.Uuid)
            pago_obj.cfe_serieNumero_pay = str(reponse.Series) + ' ' + str(reponse.Number)
            pago_obj.crearFe_Line(reponse, xmlstr, pago_id)
            pago_obj.adjuntarPdf(reponse.Pdf, pago_id)
            pago_obj.RtaCode_pay = str(reponse.RtaCode)
            pago_obj.RtaMessage_pay = str(reponse.RtaMessage)
            pago_obj.Series_pay = str(reponse.Series)
            pago_obj.Number_pay = str(reponse.Number)
            pago_obj.tipoCFE_pay = '182'
            if(self._context.get('retenciones_wiz') != False):
                pago_obj.retenciones = self._context.get('retenciones_wiz')
            if (str(reponse.RtaCode) in ('0', '-1', '1', '3', '5', '11', '12', '30', '31', '89', '96', '99')):
                pago_obj.feEstado_pay = str(reponse.RtaCode)
            else:
                pago_obj.feEstado_pay = '100'
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
            pago_obj.RtaCode_pay = str(reponse.RtaCode)
            pago_obj.RtaMessage_pay = str(reponse.RtaMessage)
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
                pago_obj.feEstado_pay = str(reponse.RtaCode)
            else:
                pago_obj.feEstado_pay = '100'

            raise ValidationError(mensaje)

            return notification

    def crearFe_Line(self, reponse2, xmlstr, pago_id):
        #print('xml', reponse2.Pdf)
        b64_pdf = base64.b64encode(reponse2.Pdf)
        name = 'pdf'
        tipoCFE_wiz = self._context.get('tipoCFE_wiz')
        if (tipoCFE_wiz == '182'):
            name = self._context.get('communication')
        else:
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

        # print('xml ATACH')
        # Crear Linea de UCFE
        ucfe_line = {
            'display_name': str(reponse2.Number),
            'Number': str(reponse2.Number),
            'Series': str(reponse2.Series),
            'RtaMessage': str(reponse2.RtaMessage),
            'RtaCode': str(reponse2.RtaCode),
            'Uuid': str(reponse2.Uuid),
            'xmlText': xmlstr,
            'pay_id': pago_id,
            'line_attachment_id': pdf_atach.id
        }
        linea = self.env['fc_pyp.fe_line'].create(ucfe_line)
        return linea

    def adjuntarPdf(self, pdf, pago_id):
        b64_pdf = base64.b64encode(pdf)
        tipoCFE_wiz = self._context.get('tipoCFE_wiz')
        name='pdf'
        if (tipoCFE_wiz == '182'):
            name = self._context.get('communication')
        else:
            name = self.name
        return self.env['ir.attachment'].create({
            'name': name,
            'type': 'binary',
            'datas': b64_pdf,
            # 'datas_fname': name + '.pdf',
            'store_fname': name,
            'res_model': self._name,
            'res_id': pago_id,
            'mimetype': 'application/pdf'
        })

    def actulizarMasivoEstadoPago(self):
        pagos_ids = self.env['account.payment'].browse(self.env.context.get('active_ids'))
        try:
            for pago in pagos_ids:
                pago.actulizarEstadoPago()
        except Exception as e:
            raise print('Error: /n' + str(e))


    def actulizarMasivoEstadoPago_Scheduler(self):
        pagos_ids = self.env['account.payment'].search([('feEstado_pay', '=', '11')])
        try:
             for pago in pagos_ids:
                 pago.actulizarEstadoPago()
        except Exception as e:
             raise ValidationError('Error: /n' + str(e))

    def actulizarEstadoPago(self):
        # Configuracion de FE Memory
        conf = self.env['fc_pyp.settings_fc'].search([('activo', '=', 'True')])
        url = str(conf.url)
        client = Client(url, wsse=UsernameToken(conf.usuario, conf.clave))
        tipoCFE = self.tipoCFE_pay
        Number = self.Number_pay
        Series = self.Series_pay
        Uuid = self.Uuid_pay
        tipoCFE_Validar = ''

        if(tipoCFE != '' and tipoCFE != False and Number != False and Series != False and Uuid != False):
            reponse = client.service.CheckCFEState(
                message={'CommerceCode': conf.comercio, 'TerminalCode': conf.terminal, 'Timeout': conf.timeout,
                         'CfeType': tipoCFE, 'Number': Number, 'Series': Series, 'Uuid': Uuid})
            RtaCodeDevuelto = str(reponse.RtaCode)
            if(RtaCodeDevuelto != self.feEstado_pay):
                self.write({
                    'feEstado_pay': RtaCodeDevuelto
                })