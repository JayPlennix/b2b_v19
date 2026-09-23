# HyperPay (OPPWA) COPYandPAY API.
TEST_DOMAIN = 'https://test.oppwa.com'
LIVE_DOMAIN = 'https://eu-prod.oppwa.com'

# Result codes, see https://wordpresshyperpay.docs.oppwa.com/reference/resultCodes
RESULT_CODES_SUCCESS = (r'^(000\.000\.|000\.100\.1|000\.[36])', r'^(000\.400\.0[^3]|000\.400\.100)')
RESULT_CODES_PENDING = (r'^(000\.200)', r'^(800\.400\.5|100\.400\.500)')

# Odoo payment method code -> COPYandPAY brand.
PAYMENT_METHODS_MAPPING = {
    'visa': 'VISA',
    'mastercard': 'MASTER',
    'amex': 'AMEX',
    'mada': 'MADA',
    'discover': 'DISCOVER',
    'jcb': 'JCB',
    'maestro': 'MAESTRO',
    'diners': 'DINERS',
}
DEFAULT_BRANDS = 'VISA MASTER'

DEFAULT_PAYMENT_METHOD_CODES = {'card', 'visa', 'mastercard'}
