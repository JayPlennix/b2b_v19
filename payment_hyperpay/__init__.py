# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    Migrated to Odoo 19.0 by Plennix Technologies for its licensee.
#
#################################################################################
from . import controllers
from . import models

from odoo.addons.payment import setup_provider, reset_payment_provider


def post_init_hook(env):
    setup_provider(env, 'hyperpay')


def uninstall_hook(env):
    reset_payment_provider(env, 'hyperpay')
