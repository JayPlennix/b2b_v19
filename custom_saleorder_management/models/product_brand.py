# -*- coding: utf-8 -*-
"""
    This model is used to create a product brand fields
"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ProductBrand(models.Model):
    _name = 'product.brand'
    _order = 'name'
    _description = 'Product Brand'

    name = fields.Char('Brand Name', required=True, translate=True)
    description = fields.Text('Description', translate=True)
    logo = fields.Binary('Logo File')
    sequence = fields.Integer(help="Gives the sequence order when displaying a list of product Brands.", index=True,
                              default=10)
    main_brand = fields.Boolean(string='Main Brand')
