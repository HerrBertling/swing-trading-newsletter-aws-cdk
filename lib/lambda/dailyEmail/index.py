from botocore.exceptions import ClientError
from datetime import datetime, timedelta
import boto3
from boto3.dynamodb.conditions import Key, Attr
from currency_converter import CurrencyConverter
import os


def handler(event, context):
    # collect data from dynamodb
    dynamodb = boto3.resource('dynamodb')
    tableName = os.environ['DATABASE']
    table = dynamodb.Table(tableName)

    marketCheckTableName = os.environ['MARKETCHECK']
    marketCheckTable = dynamodb.Table(marketCheckTableName)

    date = datetime.utcnow()

    dateString = date.strftime("%Y-%m-%d")

    marketCheckResponse = marketCheckTable.get_item(Key={'date': dateString})
    marketCheck = marketCheckResponse['Item']

    mcLastClose = marketCheck['lastClose']
    mcLastCloseString = f"{mcLastClose:.2f}"

    mcForceIndex = marketCheck['forceIndex13']
    mcForceIndexString = f"{mcForceIndex:.2f}"

    scan_kwargs = {
        'FilterExpression': Attr('entry').exists() & Key('date').eq(dateString),
    }
    done = False
    start_key = None
    items = []

    while not done:
        if start_key:
            scan_kwargs['ExclusiveStartKey'] = start_key
        validEntries = table.scan(**scan_kwargs)
        foundItems = validEntries['Items']
        items.extend(foundItems)
        start_key = validEntries.get('LastEvaluatedKey', None)
        done = start_key is None

    resultTable = ''

    resultCount = len(items)

    c = CurrencyConverter()

    for num, item in enumerate(items):
        symbol = item['symbol']
        security = item['security']
        sector = item['sector']
        entry = item['entry']['result']
        entryEuro = c.convert(entry, 'USD', 'EUR')
        entryEuroString = f"{entryEuro:.2f}"
        close = item['entry']['close']
        closeEuro = c.convert(close, 'USD', 'EUR')
        closeEuroString = f"{closeEuro:.2f}"
        rowStyle = '<tr>' if num % 2 == 0 else '<tr style="background-color: #f3f7fa;">'
        resultTable += rowStyle + '<td style="color: #1b2935; padding: 12px 0 12px 6px;vertical-align: top;"><a color: #1b2935;" href="https://de.finance.yahoo.com/quote/' + symbol + '" target=+"_blank">' + security + \
            '</a><br /><span style="font-size:0.8em">(' + symbol + ', ' + sector + ')</span></td><td style="text-align: right; color: #1b2935;padding: 12px 0;vertical-align: top;font-variant-numeric: tabular-nums;">' + \
            closeEuroString + '€</td><td style="text-align: right; color: #1b2935;padding: 12px 6px 12px 0;vertical-align: top;font-variant-numeric: tabular-nums;">' + entryEuroString + '€</td></tr>'

    sAndP500 = '<div style="font-family:Ubuntu, Helvetica, Arial, sans-serif;font-size:20px;font-weight:700;line-height:1;text-align:left;color:#2a4d69;" >S&amp;P500</div></td></tr><tr><td align="left" style="font-size:0px;padding:10px 25px;word-break:break-word;"><div style="font-family:Ubuntu, Helvetica, Arial, sans-serif;font-size:14px;line-height:1;text-align:left;color:#2a4d69;"> Close:' + mcLastCloseString + '$</div></td></tr><tr><td align="left" style="font-size:0px;padding:10px 25px;word-break:break-word;"><div style="font-family:Ubuntu, Helvetica, Arial, sans-serif;font-size:14px;line-height:1;text-align:left;color:#2a4d69;">Impulse System Weekly: ' + \
        marketCheck['weeklyImpulse'] + '</div></td></tr><tr><td align="left" style="font-size:0px;padding:10px 25px;word-break:break-word;"><div style="font-family:Ubuntu, Helvetica, Arial, sans-serif;font-size:14px;line-height:1;text-align:left;color:#2a4d69;">Impulse System Daily: ' + \
        marketCheck['dailyImpulse'] + '</div></td></tr><tr><td align="left" style="font-size:0px;padding:10px 25px;word-break:break-word;"><div style="font-family:Ubuntu, Helvetica, Arial, sans-serif;font-size:14px;line-height:1;text-align:left;color:#2a4d69;">Force Index 13 Tage: ' + mcForceIndexString + '</div>'

    emailStart = '<!doctype html><html xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office"><head><title></title><!--[if !mso]><!-- --><meta http-equiv="X-UA-Compatible" content="IE=edge"><!--<![endif]--><meta http-equiv="Content-Type" content="text/html; charset=UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style type="text/css">#outlook a { padding:0; }body { margin:0;padding:0;-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%; } table, td { border-collapse:collapse;mso-table-lspace:0pt;mso-table-rspace:0pt; }img { border:0;height:auto;line-height:100%; outline:none;text-decoration:none;-ms-interpolation-mode:bicubic; } p { display:block;margin:13px 0; }</style><!--[if mso]><xml><o:OfficeDocumentSettings><o:AllowPNG/><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml><![endif]--><!--[if lte mso 11]><style type="text/css">.mj-outlook-group-fix { width:100% !important; }</style><![endif]--><style type="text/css">@media only screen and (min-width:480px) {.mj-column-per-100 { width:100% !important; max-width: 100%; }.mj-column-per-50 { width:50% !important; max-width: 50%; }}</style><style type="text/css"></style></head><body><div><!--[if mso | IE]><table align="center" border="0" cellpadding="0" cellspacing="0" class="" style="width:600px;" width="600" ><tr><td style="line-height:0px;font-size:0px;mso-line-height-rule:exactly;"><![endif]--><div style="margin:0px auto;max-width:600px;"><table align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="width:100%;"><tbody><tr><td style="direction:ltr;font-size:0px;padding:20px 0;text-align:center;"><!--[if mso | IE]><table role="presentation" border="0" cellpadding="0" cellspacing="0"><tr><td class="" style="vertical-align:top;width:600px;" ><![endif]--><div class="mj-column-per-100 mj-outlook-group-fix" style="font-size:0px;text-align:left;direction:ltr;display:inline-block;vertical-align:top;width:100%;"><table border="0" cellpadding="0" cellspacing="0" role="presentation" style="vertical-align:top;" width="100%"><tr><td align="left" style="font-size:0px;padding:10px 25px;word-break:break-word;"><div style="font-family:Ubuntu, Helvetica, Arial, sans-serif;font-size:24px;line-height:1;text-align:left;color:#4b86b4;">Guten Morgen 👋</div></td></tr><tr><td align="left" style="font-size:0px;padding:10px 25px;word-break:break-word;"><div style="font-family:Ubuntu, Helvetica, Arial, sans-serif;font-size:14px;line-height:1;text-align:left;color:#1b2935;">Hier ist deine tägliche Markt-Übersicht 😊 – für Feedback einfach auf diese Mail antworten!</div></td></tr></table></div><!--[if mso | IE]></td></tr></table><![endif]--></td></tr></tbody></table></div><!--[if mso | IE]></td></tr></table><table align="center" border="0" cellpadding="0" cellspacing="0" class="" style="width:600px;" width="600" ><tr><td style="line-height:0px;font-size:0px;mso-line-height-rule:exactly;"><![endif]--><div style="background:#e7eff6;background-color:#e7eff6;margin:0px auto;border-radius:8px;max-width:600px;"><table align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="background:#e7eff6;background-color:#e7eff6;width:100%;border-radius:8px;"><tbody><tr><td style="direction:ltr;font-size:0px;padding:20px 0;text-align:center;"><!--[if mso | IE]><table role="presentation" border="0" cellpadding="0" cellspacing="0"><tr><td class="" style="vertical-align:top;width:300px;" ><![endif]--><div class="mj-column-per-50 mj-outlook-group-fix" style="font-size:0px;text-align:left;direction:ltr;display:inline-block;vertical-align:top;width:100%;"><table border="0" cellpadding="0" cellspacing="0" role="presentation" width="100%"><tbody><tr><td style="vertical-align:top;padding:8px;"><table border="0" cellpadding="0" cellspacing="0" role="presentation" width="100%"><tr><td align="left" style="font-size:0px;padding:10px 25px;word-break:break-word;"><div style="font-family:Ubuntu, Helvetica, Arial, sans-serif;font-size:20px;font-weight:700;line-height:1;text-align:left;color:#2a4d69;">Marktlage</div></td></tr><tr><td align="left" style="font-size:0px;padding:10px 25px;word-break:break-word;"><div style="font-family:Ubuntu, Helvetica, Arial, sans-serif;font-size:14px;line-height:1;text-align:left;color:#2a4d69;">VIX: n/a (kommt)</div></td></tr></table></td></tr></tbody></table></div><!--[if mso | IE]></td><td class="" style="vertical-align:top;width:300px;" ><![endif]--><div class="mj-column-per-50 mj-outlook-group-fix" style="font-size:0px;text-align:left;direction:ltr;display:inline-block;vertical-align:top;width:100%;"><table border="0" cellpadding="0" cellspacing="0" role="presentation" width="100%"><tbody><tr><td style="vertical-align:top;padding:8px;"><table border="0" cellpadding="0" cellspacing="0" role="presentation" width="100%"><tr><td align="left" style="font-size:0px;padding:10px 25px;word-break:break-word;">'

    emailMiddle = '</td></tr></table></td></tr></tbody></table></div><!--[if mso | IE]></td></tr></table><![endif]--></td></tr></tbody></table></div><!--[if mso | IE]></td></tr></table><table align="center" border="0" cellpadding="0" cellspacing="0" class="" style="width:600px;" width="600" ><tr><td style="line-height:0px;font-size:0px;mso-line-height-rule:exactly;"><![endif]--><div style="margin:0px auto;max-width:600px;"><table align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="width:100%;"><tbody><tr><td style="direction:ltr;font-size:0px;padding:20px 0;text-align:center;"><!--[if mso | IE]><table role="presentation" border="0" cellpadding="0" cellspacing="0"><tr><td class="" style="vertical-align:top;width:600px;" ><![endif]--><div class="mj-column-per-100 mj-outlook-group-fix" style="font-size:0px;text-align:left;direction:ltr;display:inline-block;vertical-align:top;width:100%;"><table border="0" cellpadding="0" cellspacing="0" role="presentation" style="vertical-align:top;" width="100%"><tr><td align="left" style="font-size:0px;word-break:break-word;"><div style="font-family:Ubuntu, Helvetica, Arial, sans-serif;font-size:20px;line-height:1;text-align:left;color:#2a4d69;">Treffer heute: '

    emailEnd = '</td></tr></table></div><!--[if mso | IE]></td></tr></table><![endif]--></td></tr></tbody></table></div><!--[if mso | IE]></td></tr></table><table align="center" border="0" cellpadding="0" cellspacing="0" class="" style="width:600px;" width="600" ><tr><td style="line-height:0px;font-size:0px;mso-line-height-rule:exactly;"><![endif]--><div style="background:#adcbe3;background-color:#adcbe3;margin:0px auto;max-width:600px;"><table align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="background:#adcbe3;background-color:#adcbe3;width:100%;"><tbody><tr><td style="direction:ltr;font-size:0px;padding:20px 0;text-align:center;"><!--[if mso | IE]><table role="presentation" border="0" cellpadding="0" cellspacing="0"><tr><td class="" style="vertical-align:top;width:600px;" ><![endif]--><div class="mj-column-per-100 mj-outlook-group-fix" style="font-size:0px;text-align:left;direction:ltr;display:inline-block;vertical-align:top;width:100%;"><table border="0" cellpadding="0" cellspacing="0" role="presentation" style="vertical-align:top;" width="100%"><tr><td align="left" style="font-size:0px;word-break:break-word;"><div style="font-family:Ubuntu, Helvetica, Arial, sans-serif;font-size:12px;line-height:1.4;text-align:left;color:#2a4d69;">Legal: Das hier sind keine Investitions-Empfehlungen. Bitte checke alle Aktien selbst eingehend, bevor du deine eigenständige Investitionsentscheidung triffst. Diese E-Mail ist nur eine Hilfestellung, um eventuell interessante Aktien ausfindig zu machen. Falls du dich abmelden möchtest, antworte bitte einfach auf diese E-Mail. Einen richtigen Abmeldelink gibt es demnächst, so ist das mit Beta-Phasen… Und jetzt: Have fun.</div></td></tr></table></div><!--[if mso | IE]></td></tr></table><![endif]--></td></tr></tbody></table></div><!--[if mso | IE]></td></tr></table><![endif]--></div></body></html>'

    SENDER = THIS_NEEDS_A_SENDER

    RECIPIENTS = [FILL_IN_EMAILS_HERE]

    # Specify a configuration set. If you do not want to use a configuration
    # set, comment the following variable, and the
    # ConfigurationSetName=CONFIGURATION_SET argument below.
    # CONFIGURATION_SET = "ConfigSet"

    AWS_REGION = SET_A_REGION_HERE

    # The subject line for the email.
    SUBJECT = "Deine tägliche Übersicht"

    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = ("Test\r\n"
                 "Eine testmail"
                 )

    # The HTML body of the email.
    BODY_HTML = f"""{emailStart}{sAndP500}{emailMiddle}{resultCount}</div></td></tr><tr><td align="left" style="font-size:0px;padding:10px 25px;word-break:break-word;"><table cellpadding="0" cellspacing="0" width="100%" border="0" style="color:#000000;font-family:Ubuntu, Helvetica, Arial, sans-serif;font-size:13px;line-height:22px;table-layout:auto;width:100%;border:none;"><thead><tr><th style="text-align: left; color: #4b86b4">Aktie</th><th style="text-align: right; color: #4b86b4">Close gestern</th><th style="text-align: right; color: #4b86b4">Möglicher Einstiegspreis</th></tr></thead><tbody>{resultTable}</tbody></table>{emailEnd}"""

    # The character encoding for the email.
    CHARSET = "UTF-8"

    # Create a new SES resource and specify a region.
    client = boto3.client('ses', region_name=AWS_REGION)

    # Try to send the email.
    try:
        # Provide the contents of the email.
        response = client.send_email(
            Destination={
                'BccAddresses': RECIPIENTS,
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': BODY_HTML,
                    },
                    'Text': {
                        'Charset': CHARSET,
                        'Data': BODY_TEXT,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=SENDER,
            # If you are not using a configuration set, comment or delete the
            # following line
            # ConfigurationSetName=CONFIGURATION_SET,
        )
    # Display an error if something goes wrong.
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])

        # put good results into email body
